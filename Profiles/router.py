from fastapi import APIRouter, Depends, HTTPException

from Database.database import DB
from tools.verify_token import get_current_user
from users.validation import UpdateNickName

profiles_router = APIRouter()


# 更新资料
@profiles_router.put("/update_nickname")
async def update_nickname(nickName: UpdateNickName, current_user_id: str = Depends(get_current_user)):
    User_Repo = DB.get_User_repo()

    # 根据用户 ID 查找用户文档
    user_doc = await User_Repo.find_one({"_id": current_user_id})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    # 更新昵称
    await User_Repo.update_one(
        {"_id": current_user_id},
        {"$set": {"nickName": nickName.nickName}}
    )

    return {"message": "Nickname updated successfully"}


# 查看我的收藏
@profiles_router.get("/bookmarks")
async def get_bookmarked_majors(current_user_id: str = Depends(get_current_user)):
    User_Repo = DB.get_User_repo()
    Fach_Repo = DB.get_Fach_repo()

    # 根据用户 ID 查找用户文档
    user_doc = await User_Repo.find_one({"_id": current_user_id})
    if not user_doc:
        return {"error": "User not found"}

    # 获取收藏的专业 ID 列表
    bookmarked_major_ids = user_doc.get("favorite_major_ids", [])

    # 根据专业 ID 列表查询专业信息
    bookmarked_majors = []
    for major_id in bookmarked_major_ids:
        major_doc = await Fach_Repo.find_one({"_id": major_id})
        if major_doc:
            bookmarked_majors.append(major_doc)

    return bookmarked_majors
