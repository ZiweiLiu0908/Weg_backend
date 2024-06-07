from fastapi import APIRouter
from datetime import datetime, timedelta

from Database.database import DB
from tools.test_message import sendMessage
from users.PIN.Schema.PIN_Schema import PINCode  # 引入之前定义的Pydantic模型

from tools.generate_code import generate_verification_code
from .validation import PhoneSchema

pin_router = APIRouter()



@pin_router.post("/send_code")
async def send_code(phone_data: PhoneSchema):
    phone = phone_data.phoneNumber
    PIN_Repo = DB.get_PIN_repo()
    await PIN_Repo.delete_many({'phone': phone})


    # 生成验证码
    code = generate_verification_code()

    # 定义验证码的有效期（例如5分钟）
    expires_delta = timedelta(minutes=5)

    # 创建验证码文档
    verification_doc = PINCode(
        phone=phone,
        code=code,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + expires_delta
    )

    # 存储到数据库
    await PIN_Repo.insert_one(verification_doc.dict(by_alias=True))

    # 模拟发送验证码操作（实际项目中应调用短信服务API）
    sendMessage(phoneNumber=phone, code=code)
    print(f"发送验证码到 {phone}: 验证码是 {code}")

    return {"message": "验证码发送成功", "phone": phone, "expires_at": verification_doc.expires_at}
