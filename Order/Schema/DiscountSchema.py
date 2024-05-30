from enum import Enum
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, Field
from datetime import datetime
import pytz
from Order.Schema.OrderSchema import get_beijing_time
from Database.PyObjectId import PyObjectId


class DiscountCodeSchema(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=get_beijing_time)  # 这里使用北京时间
    expired_at: Optional[datetime] = None
    used_at: Optional[datetime] = None
    user_id: Optional[str] = None
    discount_value: Optional[float] = None
    discount_percent: Optional[float] = None
    discount_type: str
    discount_code: str
    limit_times: Field(default=int) = 1

    def is_expired(self):
        if self.expired_at is None:
            return False  # 如果没有设置过期时间，认为不过期
        return self.expired_at < datetime.now(pytz.timezone('Asia/Shanghai'))

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: lambda oid: str(oid),
            datetime: lambda dt: dt.isoformat(),
        }


class DiscountType(str, Enum):
    FIXED = "fixed"  # 直接减去的金额
    PERCENTAGE = "percentage"  # 减百分比
