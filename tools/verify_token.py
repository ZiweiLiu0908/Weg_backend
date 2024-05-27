from bson import ObjectId
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from Database.database import DB

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/users/login')

SECRET_KEY = "a_very_secret_key"
ALGORITHM = "HS256"


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        user_id = ObjectId(user_id)
        # 获取令牌创建时间
        token_issued_at = payload.get("iat")
        User_repo = DB.get_User_repo()
        user = await User_repo.find_one({'_id': user_id})
        # 如果令牌的创建时间早于 password_changed_at,则认证失败
        if not user or token_issued_at < user['password_changed_at'].timestamp():
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    return str(user_id)
