from datetime import datetime
from enum import Enum
from typing import List

from motor.motor_asyncio import AsyncIOMotorClient

from Order.Schema.OrderSchema import OrderStatus, OrderSchema


# MongoDB连接配置
class Database:
    client: AsyncIOMotorClient = None

    @classmethod
    async def initialize(cls, uri, db_name):
        cls.client = AsyncIOMotorClient(uri)
        cls.db = cls.client[db_name]

    @classmethod
    async def close_mongo_connection(cls):
        cls.client.close()

    @classmethod
    def get_PIN_repo(cls):
        return cls.db['PIN']

    @classmethod
    def get_User_repo(cls):
        return cls.db['User']

    @classmethod
    def get_Uni_repo(cls):
        return cls.db['Uni']

    @classmethod
    def get_Fach_repo(cls):
        return cls.db['Fach']

    @classmethod
    def get_Transcript_repo(cls):
        return cls.db['Transcript']

    @classmethod
    def get_MatchResult_repo(cls):
        return cls.db['MatchSchema']

    @classmethod
    def get_FachRecordSchema_repo(cls):
        return cls.db['FachRecordSchema']

    @classmethod
    def get_OrderSchema_repo(cls):
        return cls.db['OrderSchema']

    @classmethod
    async def find_unpaid_orders(cls, current_time: datetime) -> List[OrderSchema]:
        collection = cls.get_OrderSchema_repo()
        query = {
            "status": OrderStatus.NOT_PAID,
            "expired_at": {"$gt": current_time}
        }
        cursor = collection.find(query)
        orders = []
        async for order in cursor:
            orders.append(OrderSchema(**order))
        return orders


    @classmethod
    def get_DiscountCodeSchema_repo(cls):
        return cls.db['DiscountCodeSchema']


DB = Database()
