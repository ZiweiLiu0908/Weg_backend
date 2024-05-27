from bson import ObjectId
from datetime import datetime
from pydantic import BaseModel, Field
from Database.PyObjectId import PyObjectId
from enum import Enum


class Role(str, Enum):
    USER = "一般用户"
    ADMIN = "管理员"


class User(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    phone: str
    nick_name: str = Field(default="匿名用户")
    profile_photo: str = ''
    password: str
    order_ids: list[str] = []
    favorite_major_ids: list[str] = []
    transcript_ids: list[str] = []
    ai_match_ids: list[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    password_changed_at: datetime = Field(default_factory=datetime.utcnow)
    role: Role = Field(default=Role.USER)  # 默认角色为一般用户
    AI_match_remain_times: int = 0
    black_list: bool = Field(default=False)
    ai_match_remain_times: int = Field(default=0)  # ai 匹配剩余次数

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: lambda oid: str(oid),
        }
