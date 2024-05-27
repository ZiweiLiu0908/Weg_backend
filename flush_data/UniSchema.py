from enum import Enum
from typing import List, Optional

from bson import ObjectId
from pydantic import BaseModel, HttpUrl, Field
from datetime import date, datetime

from database import PyObjectId



class Uni(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    logo: str  # 大学图标logo的URL
    name_cn: str  # 大学名称（中文）
    name_de: str  # 大学名称（德语）
    rank: List[str]
    is_tu9: bool
    is_elite: bool
    # intro_cn: str  # 大学中文简介
    images: List[str] = []  # 学校图片URL列表
    offical_website: str
    # advantage: str
    major_ids: List[str] = []  # 对应的专业ID列表

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: lambda oid: str(oid),
            datetime: lambda dt: dt.isoformat(),
        }
