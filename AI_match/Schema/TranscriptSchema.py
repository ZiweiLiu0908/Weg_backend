from bson import ObjectId
from pydantic import BaseModel, Field

from typing import List, Dict
from datetime import datetime
from Database.PyObjectId import PyObjectId


class Transcript(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    name: str = Field(default_factory=lambda: datetime.now().strftime("%m月%d日-%H:%M"))  # 设置默认值为当前时间的字符串
    content: List[Dict] = None
    upload_time: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: lambda oid: str(oid),
            datetime: lambda dt: dt.isoformat(),
        }
