from bson import ObjectId
from fastapi import HTTPException


async def verify_admin(user_repo, user_id: str):
    user = await user_repo.find_one({'_id': ObjectId(user_id)})
    if user['role'] != '管理员':
        # raise HTTPException(status_code=403, detail="权限不足，只有管理员可以执行此操作")
        return False, user
    return True, user