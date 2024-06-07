import asyncio
import json
from datetime import datetime, timedelta

from bson import ObjectId

from Database.database import DB
from Order.Schema.OrderSchema import OrderStatus, sendOrder
import pytz
from tools.is_first_before_second_beijing import is_first_before_second_beijing
from wechatpay.wechat_pay_asyn import WechatPay


def get_utc_time():
    # 返回当前的 UTC 时间，带有时区信息
    return datetime.utcnow().replace(tzinfo=pytz.utc)


def ensure_utc(dt):
    """确保 datetime 对象是 'aware' 并且设置为 UTC 时区"""
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        return dt.replace(tzinfo=pytz.utc)
    return dt.astimezone(pytz.utc)


class OrderQueueManager:
    def __init__(self):
        self.queue1 = asyncio.Queue()
        self.queue2 = {}
        self.is_running_queue1 = False

    async def add_order_to_queue1(self, order_id: str, expired_at: datetime, package):
        await self.queue1.put((order_id, expired_at, package))
        if not self.is_running_queue1:
            self.is_running_queue1 = True
            asyncio.create_task(self.process_queue1())

    async def add_order_to_queue2(self, order_id: str, package):
        # 保存订单的时间和package
        self.queue2[order_id] = {'timestamp': datetime.utcnow(), 'package': package}
        # 自动在2分钟后从队列2移除订单
        asyncio.create_task(self.remove_from_queue2_after_delay(order_id, delay=120))

    async def process_queue1(self):
        Order_repo = DB.get_OrderSchema_repo()
        DiscountCode_repo = DB.get_DiscountCodeSchema_repo()
        while True:
            if self.queue1.empty():
                break

            order_id, expired_at, package = await self.queue1.get()
            if not is_first_before_second_beijing(get_utc_time(), ensure_utc(expired_at)):
                await Order_repo.update_one({'_id': ObjectId(order_id)}, {'$set': {'status': OrderStatus.EXPIRED}})
                continue

            wechatPay = WechatPay()
            try:
                is_paid = await wechatPay.wy_check_order_status(order_id)
                # print(is_paid)
                if is_paid:
                    is_paid['message'] = json.loads(is_paid['message'])
                    if is_paid['message']['trade_state'] == 'SUCCESS':
                        order = await Order_repo.find_one({'_id': ObjectId(order_id)})
                        if 'discount_code' in order.keys():
                            discount_code = order['discount_code']
                            user_id = order['user_id']
                            await DiscountCode_repo.find_one_and_update({'discount_code': discount_code},
                                                                        {'$inc': {'limit_times': -1},
                                                                         '$push': {'user_id': user_id,
                                                                                   'used_at': str(datetime.utcnow())}
                                                                         },
                                                                        )

                        if package not in ['ai1', 'ai3', 'ai8']:
                            await Order_repo.update_one({'_id': ObjectId(order_id)},
                                                        {'$set': {'status': OrderStatus.IN_PROGRESS}})
                        else:
                            await Order_repo.update_one({'_id': ObjectId(order_id)},
                                                        {'$set': {'status': OrderStatus.FINISHED}})

                        neworder = await Order_repo.find_one({'_id': ObjectId(order_id)})
                        sendOrder(neworder)
                        await self.add_order_to_queue2(order_id, package)

                    else:
                        await self.queue1.put((order_id, expired_at, package))

            except Exception as e:
                print(f"Error checking order status for {order_id}: {e}")

            await asyncio.sleep(5)

        self.is_running_queue1 = False

    async def remove_from_queue2(self, order_id: str):
        if order_id in self.queue2:
            del self.queue2[order_id]

    async def remove_from_queue2_after_delay(self, order_id: str, delay: int):
        await asyncio.sleep(delay)
        await self.remove_from_queue2(order_id)

    async def find_and_remove_from_queue2(self, order_id: str) -> (bool, str):
        if order_id in self.queue2:
            package = self.queue2[order_id]['package']
            await self.remove_from_queue2(order_id)
            return True, package
        return False, None


order_manager = OrderQueueManager()
