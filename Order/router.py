from bson import ObjectId
from fastapi import APIRouter, Depends

from Order.OrderManage.OrderManager import OrderManager
from Order.Schema.OrderSchema import OrderSchema, OrderStatus
from Order.validation import CreateOrderSchema, getOneOrderStatusSchema, AdminRefundDecisionSchema
from Database.database import DB
from tools.verify_token import get_current_user

orders_router = APIRouter()


# 创建新订单
@orders_router.post("/createOrder")
async def createOrder(orderInfo: CreateOrderSchema, current_user_id: str = Depends(get_current_user)):
    Order_repo = DB.get_OrderSchema_repo()

    # 查看优惠码类型
    if orderInfo.discount_code:
        DiscountCode_repo = DB.get_DiscountCodeSchema_repo()
        discount_code = orderInfo.discount_code
        discount_code = await DiscountCode_repo.find_one({'discount_code': discount_code})
        if not discount_code or discount_code.is_expired() or discount_code['limit_times'] <= 0:
            return {"status": "failed", "message": "优惠码无效", 'couponIsValid': False}

        # 创建订单
        package = orderInfo.package_tc
        newOrder = OrderSchema(
            user_id=current_user_id,
            package=package,
            discount_value=discount_code.discount_value,
            discount_percent=discount_code.discount_percent,
        )
    else:
        package = orderInfo.package_tc
        newOrder = OrderSchema(
            user_id=current_user_id,
            package=package,
        )
    newOrderEntity = await Order_repo.insert_one(newOrder.dict(by_alias=True))
    # print(newOrder)

    # 调用创建支付函数（从WY获取支付二维码）
    QR_code = None
    order = None
    # QR_code = await wy_create_payment(str(newOrder.inserted_id), price=newOrder.real_price)
    if QR_code:
        order = await Order_repo.update_one({'_id': newOrderEntity.inserted_id}, {'$set': {'QR_code': QR_code}})

    # 加入第一个队列，每隔5分钟检查一次该订单是否支付成功，超过16分钟未支付则移出
    order_manager = OrderManager()
    await order_manager.add_order_to_queue1(str(newOrderEntity.inserted_id), newOrder.expired_at)

    return {"message": "create success", "QR_code": QR_code, 'OrderId': str(newOrderEntity.inserted_id), 'order': order}


# 查看用户的所有订单的状态
@orders_router.get("/getAllMyOrders")
async def getAllMyOrders(current_user_id: str = Depends(get_current_user)):
    Order_repo = DB.get_OrderSchema_repo()
    orders = await Order_repo.find({"user_id": current_user_id})
    if not orders:
        orders = []
    return {"status": "success", "orders": orders}


# 查看用户的特定订单状态
@orders_router.post("/getOneOrderStatus")
async def getOneOrderStatus(orderInfo: getOneOrderStatusSchema, current_user_id: str = Depends(get_current_user)):
    Order_repo = DB.get_OrderSchema_repo()
    order = await Order_repo.find_one({'_id': ObjectId(orderInfo.orderid)})
    if not order:
        return {"status": "fail", "message": '订单不存在'}
    if order.user_id != current_user_id:
        return {"status": "fail", "message": '无权限访问'}
    order_manager = OrderManager()
    is_in_queue2 = await order_manager.find_and_remove_from_queue2(orderInfo.orderid)
    order_status = OrderStatus.IN_PROGRESS if is_in_queue2 else OrderStatus.NOT_PAID
    # 查看是否在队列2中，有则返回成功。无则返回等待支付
    return {"status": "success", "orderStatus": order_status}


# 用户申请特定订单的退款
@orders_router.post("/applyReturn")
async def applyReturn(orderInfo: getOneOrderStatusSchema, current_user_id: str = Depends(get_current_user)):
    Order_repo = DB.get_OrderSchema_repo()
    order = await Order_repo.find_one({'_id': ObjectId(orderInfo.orderid)})
    if not order:
        return {"status": "fail", "message": '订单不存在'}
    if order.user_id != current_user_id:
        return {"status": "fail", "message": '无权限访问'}
    if order.status != OrderStatus.IN_PROGRESS:
        return {"status": "fail", "message": '订单未支付或已完成，无法退款'}
    await Order_repo.update_one({"_id": ObjectId(orderInfo.orderid)}, {"$set": {"status": OrderStatus.RETURNING}})
    return {'message': "申请退款中", "orderStatus": OrderStatus.RETURNING}


# # wechat回调地址，通知某个order支付结果（交给WY处理）
# @orders_router.post("/WechatNotifyOrderStatus")
# async def WechatNotifyOrderStatus():
#     Order_repo = DB.get_OrderSchema_repo()

# 管理员对“申请退款”的同意或拒绝
@orders_router.post("/admin/refundDecision")
async def admin_refund_decision(decisionInfo: AdminRefundDecisionSchema,
                                current_user_id: str = Depends(get_current_user)):
    # 验证当前用户是否为管理员
    User_repo = DB.get_User_repo()
    user = await User_repo.find_one({'_id': ObjectId(current_user_id)})
    if user.role != '管理员':
        return {"status": "failed", "message": "无权限"}

    # 查找订单并验证状态
    Order_repo = DB.get_OrderSchema_repo()
    order = await Order_repo.find_one({'_id': ObjectId(decisionInfo.orderid)})
    if not order:
        return {"status": "fail", "message": '订单不存在'}
    if order['status'] != OrderStatus.RETURNING:
        return {"status": "fail", "message": '订单当前不在申请退款状态'}

    # 根据管理员的决策更新订单状态
    if decisionInfo.decision == "approve":
        # wy_return_money(orderid, order.real_price)
        new_status = OrderStatus.RETURNED
    elif decisionInfo.decision == "reject":
        new_status = OrderStatus.RETURNFAILED
    else:
        return {"status": "fail", "message": '无效的决策'}

    await Order_repo.update_one({"_id": ObjectId(decisionInfo.orderid)}, {"$set": {"status": new_status}})
    return {"status": "success", "newStatus": new_status}


# 管理员查看“申请退款RETURNING”状态中的订单
@orders_router.get("/admin/viewReturningOrders")
async def admin_view_returning_orders(current_user_id: str = Depends(get_current_user)):
    # 验证当前用户是否为管理员
    User_repo = DB.get_User_repo()
    user = await User_repo.find_one({'_id': ObjectId(current_user_id)})
    if user.role != '管理员':
        return {"status": "failed", "message": "无权限"}

    # 查找所有状态为RETURNING的订单
    Order_repo = DB.get_OrderSchema_repo()
    returning_orders = await Order_repo.find({"status": OrderStatus.RETURNING})
    if not returning_orders:
        returning_orders = []
    return {"status": "success", "orders": returning_orders}
