from bson import ObjectId
from fastapi import APIRouter, Depends

from Database.database import DB
from tools.verify_token import get_current_user

admin_router = APIRouter()


@admin_router.delete("/deleteUser")
async def checkStatus(blockUserId: str, current_user_id: str = Depends(get_current_user)):
    User_repo = DB.get_User_repo()
    user = User_repo.find_one({'_id': ObjectId(current_user_id)})
    if user.role == '管理员':
        await User_repo.update_one(
            {"_id": ObjectId(blockUserId)},
            {"$set": {"blackList": True}}
        )

    return {'status': 'success', 'id': blockUserId}