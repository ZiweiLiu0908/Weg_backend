from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, Field
from datetime import datetime

from Order.Schema.OrderSchema import get_beijing_time
from Database.PyObjectId import PyObjectId


class DiscountCodeSchema(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=get_beijing_time)  # 这里使用北京时间
    created_by: str  # admin id
    discount_value: Optional[float] = None
    discount_percent: Optional[float] = None
    discount_code: str
    used_at: Optional[datetime]
    used_by: str  # user id


    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: lambda oid: str(oid),
            datetime: lambda dt: dt.isoformat(),
        }
