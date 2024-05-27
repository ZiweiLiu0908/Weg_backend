# 生成令牌的函数
from datetime import datetime, timedelta
from jose import jwt
from jose.exceptions import JWTError

# 假设你已经有了SECRET_KEY和ALGORITHM
SECRET_KEY = "a_very_secret_key"
ALGORITHM = "HS256"


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=365)
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow()  # 添加此行
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
