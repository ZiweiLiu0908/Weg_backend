from bson import ObjectId
from pydantic import BaseModel, Field
from datetime import datetime
from Database.database import PyObjectId



class FachRecordSchema(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    uni_name: str
    fach_ch_name: str
    fach_en_name: str
    content: str

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: lambda oid: str(oid),
            datetime: lambda dt: dt.isoformat(),
        }
