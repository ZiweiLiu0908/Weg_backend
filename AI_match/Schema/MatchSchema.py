from bson import ObjectId
from pydantic import BaseModel, Field
from datetime import datetime
from Database.PyObjectId import PyObjectId
from enum import Enum


class StatusEnum(str, Enum):
    进行中 = "进行中"
    失败 = "失败"
    已完成 = "已完成"


class MatchSchema(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    trans_id: str
    fach_record_id: str
    uni_cn_name: str
    fach_en_cn_name: str
    name: str = Field(default_factory=lambda: datetime.now().strftime("%m月%d日-%H:%M"))  # 设置默认值为当前时间的字符串
    result: str = Field(default="")
    status: StatusEnum = Field(default=StatusEnum.进行中)
    upload_time: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: lambda oid: str(oid),
            datetime: lambda dt: dt.isoformat(),
        }
