from pydantic import BaseModel, Field

class PhoneSchema(BaseModel):
    phoneNumber: str = Field(..., example="1234567890")
