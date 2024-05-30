import secrets
import string
from datetime import timedelta
from typing import Any, Dict, List

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from Admin.validation import DateRange, CreateDiscountCode
from Database.database import DB
from Order.Schema.DiscountSchema import DiscountType, DiscountCodeSchema
from Order.Schema.OrderSchema import get_beijing_time
from tools.get_time_filter import get_time_filter
from tools.verify_admin import verify_admin
from tools.verify_token import get_current_user

admin_router = APIRouter()


@admin_router.delete("/deleteUser")
async def checkStatus(blockUserId: str, current_user_id: str = Depends(get_current_user)):
    User_repo = DB.get_User_repo()
    res, user = await verify_admin(User_repo, current_user_id)
    if res:
        await User_repo.update_one(
            {"_id": ObjectId(blockUserId)},
            {"$set": {"blackList": True}}
        )
        return {'status': 'success', 'id': blockUserId}
    else:
        return {'status': 'fail', 'message': '无操作权限'}


# 统计用户注册数量
@admin_router.get("/user_registration_count")
async def user_registration_count(dataRange: DateRange, current_user_id: str = Depends(get_current_user)):
    User_repo = DB.get_User_repo()
    await verify_admin(User_repo, current_user_id)

    time_filter = get_time_filter(dataRange)
    count = await User_repo.count_documents(time_filter)

    return {"start_date": dataRange.start_date, "end_date": dataRange.end_date, "count": count}


# 分析套餐购买情况
async def package_statistics(dataRange: DateRange, current_user_id: str = Depends(get_current_user)) -> List[Dict[str, Any]]:
    User_repo = DB.get_User_repo()
    Order_repo = DB.get_OrderSchema_repo()

    # 验证当前用户是否是管理员
    await verify_admin(User_repo, current_user_id)

    # 创建时间过滤器
    created_time_filter = get_time_filter(dataRange, "created_at")
    pay_time_filter = get_time_filter(dataRange, "pay_time")
    apply_return_time_filter = get_time_filter(dataRange, "apply_return_time")
    returned_time_filter = get_time_filter(dataRange, "returned_time")

    # 聚合查询，统计各个套餐的订单创建数量及总金额
    def create_pipeline(filter_stage, count_key, amount_key):
        return [
            {"$match": filter_stage},
            {
                "$group": {
                    "_id": "$package",
                    count_key: {"$sum": 1},
                    amount_key: {"$sum": "$real_price"}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "package": "$_id",
                    count_key: 1,
                    amount_key: 1
                }
            }
        ]

    created_pipeline = create_pipeline(created_time_filter, "total_created_count", "total_created_amount")
    paid_pipeline = create_pipeline(pay_time_filter, "total_paid_count", "total_paid_amount")
    apply_return_pipeline = create_pipeline(apply_return_time_filter, "total_apply_return_count",
                                            "total_apply_return_amount")
    returned_pipeline = create_pipeline(returned_time_filter, "total_returned_count", "total_returned_amount")

    created_results = await Order_repo.aggregate(created_pipeline).to_list(length=None)
    paid_results = await Order_repo.aggregate(paid_pipeline).to_list(length=None)
    apply_return_results = await Order_repo.aggregate(apply_return_pipeline).to_list(length=None)
    returned_results = await Order_repo.aggregate(returned_pipeline).to_list(length=None)

    # 合并结果
    def merge_results(base, additional, count_key, amount_key):
        additional_dict = {item["package"]: item for item in additional}
        for item in base:
            additional_item = additional_dict.get(item["package"], {})
            item[count_key] = additional_item.get(count_key, 0)
            item[amount_key] = additional_item.get(amount_key, 0.0)
        return base

    merged_results = merge_results(created_results, paid_results, "total_paid_count", "total_paid_amount")
    merged_results = merge_results(merged_results, apply_return_results, "total_apply_return_count",
                                   "total_apply_return_amount")
    merged_results = merge_results(merged_results, returned_results, "total_returned_count", "total_returned_amount")

    return merged_results


# 生成一个优惠码
async def generate_unique_code(length=8):
    """生成一个不包含O、0、I、1且字母大写的独一无二的优惠码"""
    alphabet = string.ascii_uppercase.replace('O', '').replace('I', '') + string.digits.replace('0', '').replace('1',
                                                                                                                 '')
    while True:
        code = ''.join(secrets.choice(alphabet) for _ in range(length))
        if not await discount_code_exists(code):
            return code


# 判断优惠码是否在数据库中
async def discount_code_exists(code):
    """检查优惠码是否已经存在"""
    DiscountCode_repo = DB.get_DiscountCodeSchema_repo()
    existing_code = await DiscountCode_repo.find_one({"discount_code": code})
    return existing_code is not None


# 管理员创建优惠码
@admin_router.post("/create_discount_code")
async def create_discount_code(inputInfo: CreateDiscountCode, current_user_id: str = Depends(get_current_user)):
    discount_amount = inputInfo.discount_amount
    discount_type = inputInfo.discount_type
    validity_days = inputInfo.validity_days
    limit_times = inputInfo.limit_times

    User_repo = DB.get_User_repo()
    res, user = await verify_admin(User_repo, current_user_id)
    if not res:
        return {'status': 'failed', 'message': '无权限'}

    discount_code = await generate_unique_code()  # 生成唯一的优惠码

    if discount_type == DiscountType.FIXED:
        discount_value = discount_amount
        discount_percent = None
    elif discount_type == DiscountType.PERCENTAGE:
        discount_value = None
        discount_percent = discount_amount
    else:
        raise HTTPException(status_code=400, detail="无效的折扣类型")

    created_at = get_beijing_time()
    expired_at = created_at + timedelta(days=validity_days)

    discount_code_data = DiscountCodeSchema(
        discount_value=discount_value,
        discount_percent=discount_percent,
        discount_type=discount_type,
        discount_code=discount_code,
        created_at=created_at,
        expired_at=expired_at,
        limit_times=limit_times,
    )

    DiscountCode_repo = DB.get_DiscountCodeSchema_repo()
    result = await DiscountCode_repo.insert_one(discount_code_data.dict(by_alias=True))
    if not result.acknowledged:
        raise HTTPException(status_code=500, detail="创建优惠码失败")

    return {"status": "success","message": "优惠码创建成功", "discount_code": discount_code}
