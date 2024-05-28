from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from passlib.context import CryptContext  # 用于密码加密

from Database.database import DB
from tools.verify_token import get_current_user
from users.Schema.UserSchema import Role, User  # 引入用户集合和验证码集合
from tools.generateToken import create_access_token
from users.validation import CreateUserSchema, PasswordResetSchema, CreateAdminUserSchema, LoginSchema

user_router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@user_router.post("/create")
async def create_user(user: CreateUserSchema):

    PIN_Repo = DB.get_PIN_repo()
    User_Repo = DB.get_User_repo()
    # 验证验证码是否有效
    verification_record = await PIN_Repo.find_one({"phone": user.phone})

    if not verification_record or verification_record["code"] != user.code:
        raise HTTPException(status_code=400, detail="无效的验证码")

    # 检查验证码是否过期
    if verification_record["expires_at"] < datetime.utcnow():
        await PIN_Repo.delete_one({"_id": verification_record["_id"]})
        raise HTTPException(status_code=400, detail="验证码已过期")

    # 检查手机号是否已被注册
    if await User_Repo.find_one({"phone": user.phone}):
        await PIN_Repo.delete_one({"_id": verification_record["_id"]})
        raise HTTPException(status_code=401, detail="手机号已被注册")

    # 加密密码
    hashed_password = pwd_context.hash(user.password)

    # 创建用户记录
    new_user = User(
        phone=user.phone,
        password=hashed_password,
        created_at=datetime.utcnow(),
        password_changed_at=datetime.utcnow(),
    )

    # 存储到数据库
    result = await User_Repo.insert_one(new_user.dict(by_alias=True))
    # 删除验证码
    await PIN_Repo.delete_one({"_id": verification_record["_id"]})
    access_token = create_access_token(data={"sub": str(result.inserted_id)})
    # 返回创建成功的消息和Token
    return {"message": "用户创建成功", "access_token": access_token, "token_type": "bearer"}


@user_router.post("/login")
async def login_for_access_token(userInput: LoginSchema):

    User_Repo = DB.get_User_repo()

    user = await User_Repo.find_one({"phone": userInput.phone})
    if not user or not pwd_context.verify(userInput.password, user["password"]):
        raise HTTPException(
            status_code=400,
            detail="Incorrect username or password"
        )
    if user['blackList']:
        raise HTTPException(
            status_code=400,
            detail="Incorrect username or password"
        )
    print(user)
    # 生成令牌
    access_token = create_access_token(
        data={"sub": str(user['_id'])}
    )

    return {"message": '登陆成功', "access_token": access_token, "token_type": "bearer"}


@user_router.post("/reset_password")
async def reset_password(request: PasswordResetSchema):
    PIN_Repo = DB.get_PIN_repo()
    User_Repo = DB.get_User_repo()
    # 验证验证码是否有效
    verification_record = await PIN_Repo.find_one({"phone": request.phone})
    if not verification_record or verification_record["code"] != request.code:
        raise HTTPException(status_code=400, detail="无效的验证码")

    # 检查验证码是否过期
    if verification_record["expires_at"] < datetime.utcnow():
        await PIN_Repo.delete_one({"_id": verification_record["_id"]})
        raise HTTPException(status_code=400, detail="验证码已过期")

    # 检查用户是否存在
    user_record = await User_Repo.find_one({"phone": request.phone})
    if not user_record:
        await PIN_Repo.delete_one({"_id": verification_record["_id"]})
        raise HTTPException(status_code=404, detail="用户不存在")

    if user_record['blackList']:
        raise HTTPException(
            status_code=400,
            detail="Incorrect username or password"
        )

    # 加密新密码
    hashed_new_password = pwd_context.hash(request.new_password)

    # 更新用户密码和密码更改时间
    await User_Repo.update_one(
        {"_id": user_record["_id"]},
        {"$set": {"password": hashed_new_password, "password_changed_at": datetime.utcnow()}}
    )

    # 删除已使用的验证码
    await PIN_Repo.delete_one({"_id": verification_record["_id"]})

    # 生成令牌
    access_token = create_access_token(
        data={"sub": str(user_record['_id'])}
    )

    return {"message": "密码重置成功", "access_token": access_token}


@user_router.get("/checkStatus")
async def checkStatus(current_user_id: str = Depends(get_current_user)):
    return {'status': 'success', 'id': current_user_id}


@user_router.post("/create_admin")
async def create_admin_user(request: CreateAdminUserSchema):
    PIN_Repo = DB.get_PIN_repo()
    User_Repo = DB.get_User_repo()
    ADMIN_KEY = "your_very_secure_admin_key"  # 应从环境变量或更安全的地方获取
    # 验证管理员密钥
    if request.admin_key.get_secret_value() != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="无效的管理员密钥")

    # 验证验证码
    verification_record = await PIN_Repo.find_one({"phone": request.phone})
    if not verification_record or verification_record["code"] != request.code:
        raise HTTPException(status_code=400, detail="无效的验证码")

    # 检查验证码是否过期
    if verification_record["expires_at"] < datetime.utcnow():
        await PIN_Repo.delete_one({"_id": verification_record["_id"]})
        raise HTTPException(status_code=400, detail="验证码已过期")

    # 加密密码
    hashed_password = pwd_context.hash(request.password)

    # 创建管理员用户记录
    new_admin = User(
        phone=request.phone,
        password=hashed_password,
        created_at=datetime.utcnow(),
        password_changed_at=datetime.utcnow(),
        role=Role.ADMIN.value
    )

    # 存储到数据库
    new_admin = await User_Repo.insert_one(new_admin.dict(by_alias=True))

    # 删除已使用的验证码
    await PIN_Repo.delete_one({"_id": verification_record["_id"]})

    # 可以选择在这里生成和返回访问令牌
    access_token = create_access_token(data={"sub": str(new_admin.inserted_id)})

    return {"message": "管理员账户创建成功", "access_token": access_token, "token_type": "bearer"}


@user_router.get("/getUserInfo")
async def getUserInfo(current_user_id: str = Depends(get_current_user)):
    user_repo = DB.get_User_repo()
    user = await user_repo.find_one({'_id': ObjectId(current_user_id)})
    user['password'] = None
    user['_id'] = str(user['_id'])
    return {'status': 'success', 'info': user}