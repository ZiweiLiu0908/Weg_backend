from pydantic import BaseModel, Field, constr
from datetime import datetime, timedelta
from Database.PyObjectId import PyObjectId
from bson import ObjectId


class PINCode(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    phone: str  # 适用于大多数国际电话号码格式
    code: constr(min_length=6, max_length=6)  # 假设验证码长度在4到6之间
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(minutes=5))  # 假设验证码5分钟后过期

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: lambda oid: str(oid),
        }
