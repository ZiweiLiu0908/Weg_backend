import asyncio
import json
from datetime import datetime, timedelta

from Database.database import DB
from Order.Schema.OrderSchema import OrderStatus
from tools.is_first_before_second_beijing import is_first_before_second_beijing
from wechatpay.wechat_pay_asyn import WechatPay


class OrderQueueManager:
    def __init__(self):
        self.queue1 = asyncio.Queue()
        self.queue2 = {}
        self.is_running_queue1 = False

    async def add_order_to_queue1(self, order_id: str, expired_at: datetime):
        await self.queue1.put((order_id, expired_at))
        if not self.is_running_queue1:
            self.is_running_queue1 = True
            asyncio.create_task(self.process_queue1())

    async def add_order_to_queue2(self, order_id: str):
        self.queue2[order_id] = datetime.utcnow()
        # Automatically remove order from queue2 after 2 minutes
        asyncio.create_task(self.remove_from_queue2_after_delay(order_id, delay=120))

    async def process_queue1(self):
        while True:
            if self.queue1.empty():
                break

            order_id, expired_at = await self.queue1.get()
            if not is_first_before_second_beijing(datetime.utcnow(), expired_at):
                continue

            wechatPay = WechatPay()  # Ensure this is initialized here or passed appropriately
            try:
                is_paid = await wechatPay.wy_check_order_status(order_id)
                if is_paid:
                    is_paid['message'] = json.loads(is_paid['message'])
                    if is_paid['message']['trade_state'] == 'SUCCESS':
                        Order_repo = DB.get_OrderSchema_repo()
                        await Order_repo.update_one({'_id': order_id}, {'$set': {'status': OrderStatus.IN_PROGRESS}})
                        await self.add_order_to_queue2(order_id)
                    else:
                        await self.queue1.put((order_id, expired_at))

            except Exception as e:
                print(f"Error checking order status for {order_id}: {e}")

            await asyncio.sleep(10)

        self.is_running_queue1 = False

    async def remove_from_queue2(self, order_id: str):
        if order_id in self.queue2:
            del self.queue2[order_id]

    async def remove_from_queue2_after_delay(self, order_id: str, delay: int):
        await asyncio.sleep(delay)
        await self.remove_from_queue2(order_id)

    async def find_and_remove_from_queue2(self, order_id: str) -> bool:
        if order_id in self.queue2:
            await self.remove_from_queue2(order_id)
            return True
        return False


order_manager = OrderQueueManager()
