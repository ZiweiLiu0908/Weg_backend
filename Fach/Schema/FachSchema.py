from enum import Enum
from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, Field

from Database.database import PyObjectId


class DegreeType(str, Enum):
    BACHELOR = "本科"
    MASTER = "硕士"
    PHD = "博士"


class ApplicationSeason(str, Enum):
    WINTER = "冬季"
    SUMMER = "夏季"


class LanguageRequirement(BaseModel):
    german_direct: Optional[str] = None  # 直接录取德语要求
    german_conditional: Optional[str] = None  # 条件录取语言要求
    english: Optional[str] = None  # 直接录取英语要求


class FachSchema(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    UniName: str
    name_cn: str  # 专业名（中文）
    name_en: str  # 专业名（英文）
    semesterNumber: str
    admission_lang: str
    cond_admission_lang: str
    language_requirement: str
    other_requirements: str
    is_nc: str  # 是否Numerus Clausus（名额限制）
    instruction_lang: str
    degree: str  # 学位
    apply_semester: str
    tuition: str
    winter_semester_apply_time: str
    summer_semester_apply_time: str
    subject: str  # 专业分类
    field: str  # 专业方向


    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: lambda oid: str(oid),
        }
