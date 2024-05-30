from pydantic import BaseModel, constr
from pydantic import SecretStr


class CreateUserSchema(BaseModel):
    phone: str  # 使用正则表达式验证电话号码格式
    password: str  # 在实际应用中，你可能需要对密码进行更严格的验证
    code: constr(min_length=6, max_length=6)  # 确保验证码为6位数字


class LoginSchema(BaseModel):
    phone: str
    password: str


class PasswordResetSchema(BaseModel):
    phone: str  # 电话号码的验证规则
    code: constr(min_length=6, max_length=6)  # 6位数的验证码
    new_password: str  # 新密码


class CreateAdminUserSchema(BaseModel):
    admin_key: str
    phone: str
    password: str



class UpdateNickName(BaseModel):
    nickName: str