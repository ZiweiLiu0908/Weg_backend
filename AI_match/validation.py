from typing import List

from pydantic import BaseModel, root_validator


class UpdateTrans(BaseModel):
    trans_id: str  # 成绩单ID
    content: List  # 新的成绩单内容


class CreateTrans(BaseModel):
    content: List  # 新的成绩单内容


class StartMatch(BaseModel):
    trans_id: str
    fach_record_id: str


class getTransContetnSchema(BaseModel):
    trans_id: str


class MatchResultSchema(BaseModel):
    MatchResultId: str
