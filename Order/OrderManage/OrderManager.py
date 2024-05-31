import asyncio
from datetime import datetime
from typing import Dict
from bson import ObjectId

from tools.is_first_before_second_beijing import is_first_before_second_beijing
from wechatpay.wechat_pay_asyn import WechatPay
from Order.Schema.OrderSchema import get_beijing_time, OrderStatus

from Database.database import DB

wechatPay = WechatPay()
order_manager = None





class OrderManager:
    def __init__(self, loop):
        self.queue1: Dict[str, asyncio.Task] = {}
        self.queue2: Dict[str, asyncio.Task] = {}
        self.Order_repo = DB.get_OrderSchema_repo()
        self.loop = loop

    async def add_order_to_queue1(self, order_id: str, expiry_time: datetime):
        if order_id in self.queue1:
            return

        # task = asyncio.create_task(self.check_payment_status(order_id, expiry_time))
        task = self.loop.create_task(self.check_payment_status(order_id, expiry_time))
        self.queue1[order_id] = task

    async def check_payment_status(self, order_id: str, expiry_time: datetime):
        while is_first_before_second_beijing(datetime.utcnow(), expiry_time):
            print(f"Checking payment status for order {order_id}")
            try:
                is_paid = await wechatPay.wy_check_order_status(order_id)
                print(f"Payment status for order {order_id}: {is_paid}")
                if is_paid:
                    await self.update_order_status(order_id, OrderStatus.IN_PROGRESS)
                    await self.move_to_queue2(order_id)
                    return
            except Exception as e:
                print(f"Error checking payment status for order {order_id}: {e}")

            await asyncio.sleep(30)

        await self.remove_from_queue1(order_id)
        print(f"Order {order_id} removed from queue1 after expiry time")

    async def remove_from_queue1(self, order_id: str):
        task = self.queue1.pop(order_id, None)
        if task:
            task.cancel()

    async def move_to_queue2(self, order_id: str):
        await self.remove_from_queue1(order_id)
        task = asyncio.create_task(self.lifecycle_in_queue2(order_id))
        self.queue2[order_id] = task

    async def lifecycle_in_queue2(self, order_id: str):
        await asyncio.sleep(60)
        await self.remove_from_queue2(order_id)

    async def remove_from_queue2(self, order_id: str):
        task = self.queue2.pop(order_id, None)
        if task:
            task.cancel()

    async def find_and_remove_from_queue2(self, order_id: str) -> bool:
        if order_id in self.queue2:
            await self.remove_from_queue2(order_id)
            return True
        return False

    async def load_unpaid_orders(self):
        current_time = get_beijing_time()
        unpaid_orders = await self.Order_repo.find_unpaid_orders(current_time)
        for order in unpaid_orders:
            await self.add_order_to_queue1(order['_id'], order['expired_at'])

    async def update_order_status(self, order_id: str, new_status: OrderStatus):
        await self.Order_repo.update_one({"_id": ObjectId(order_id)}, {"$set": {"status": new_status}})


# 冷启动时加载未支付订单
async def cold_start():
    order_manager = OrderManager(loop=asyncio.get_event_loop())
    await order_manager.load_unpaid_orders()
