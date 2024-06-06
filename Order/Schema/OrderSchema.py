from enum import Enum
from typing import Optional, List
from Database.PyObjectId import PyObjectId
import pytz
from bson import ObjectId
from pydantic import BaseModel, Field, root_validator
from datetime import datetime, timedelta


class OrderStatus(str, Enum):
    NOT_PAID = "NOT_PAID"  # 已经创建但未付款
    EXPIRED = "EXPIRED"  # 已经过期
    IN_PROGRESS = "IN_PROGRESS"  # 已经付款 订单开始制作
    FINISHED = "FINISHED"  # 订单已经完成 （完成状态）
    RETURNING = "RETURNING"  # 订单申请退款中
    RETURNED = "RETURNED"  # 订单已经退款 （完成状态）
    RETURNFAILED = "RETURNFAILED"  # 订单退款失败


class Package(str, Enum):
    ai1 = 'ai1'
    ai3 = 'ai3'
    ai8 = 'ai8'
    one = 'one'
    two = 'two'
    three = 'three'
    four = 'four'
    five = 'five'


package_price_map = {
    'ai1': 19.99,
    'ai3': 52,
    'ai8': 128,
    'one': 24999,
    'two': 4699,
    'three': 2000,
    'four': 1000,
    'five': 2000,
}


def get_beijing_time():
    utc_dt = datetime.utcnow()  # 获取 UTC 时间
    utc_dt = utc_dt.replace(tzinfo=pytz.utc)  # 设置 UTC 时间的时区信息
    beijing_tz = pytz.timezone('Asia/Shanghai')  # 获取北京时区
    beijing_dt = utc_dt.astimezone(beijing_tz)  # 将 UTC 时间转换为北京时间
    return beijing_dt


class OrderSchema(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    created_at: datetime = Field(default_factory=get_beijing_time)
    expired_at: datetime = Field(
        default_factory=lambda: get_beijing_time() + timedelta(minutes=6))
    status: OrderStatus = OrderStatus.NOT_PAID
    package: Package
    org_price: float
    real_price: float
    discount_code: Optional[str] = None
    discount_value: Optional[float] = None
    discount_percent: Optional[float] = None
    pay_time: Optional[datetime] = None
    apply_return_time: Optional[datetime] = None
    returned_time: Optional[datetime] = None
    QR_code: str = None
    ai_total_times: Optional[int] = 0
    ai_used_times: Optional[int] = 0
    at_used_at: Optional[List[datetime]] = []

    @root_validator(pre=True)
    def set_prices_and_expired_at(cls, values):
        package = values.get('package')
        if package:
            if package in ['ai1', 'ai3', 'ai8']:
                values['ai_total_times'] = int(package[-1])

            org_price = package_price_map.get(package)
            values['org_price'] = org_price

            discount_value = values.get('discount_value')
            discount_percent = values.get('discount_percent')

            if discount_value is not None:
                values['real_price'] = org_price - discount_value
                # values['discount_percent'] = round((discount_value / org_price) * 100, 2)
            elif discount_percent is not None:
                values['real_price'] = org_price * (1 - discount_percent / 100)
                # values['discount_value'] = round(org_price * (discount_percent / 100), 2)
            else:
                values['real_price'] = org_price  # 如果没有折扣，则实际价格等于原价

        if 'created_at' in values and 'expired_at' not in values:
            values['expired_at'] = values['created_at'] + timedelta(minutes=16)
        return values

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: lambda oid: str(oid),
            datetime: lambda dt: dt.isoformat(),
        }
