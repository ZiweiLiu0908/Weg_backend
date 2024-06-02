import json
from datetime import datetime, timedelta

import pytz
from bson import ObjectId
from fastapi import APIRouter, Depends
from fastapi import Response, status, Request
from Order.OrderManage.OrderQueueManager import order_manager
from Order.Schema.OrderSchema import OrderSchema, OrderStatus, get_beijing_time
from Order.validation import CreateOrderSchema, getOneOrderStatusSchema, AdminRefundDecisionSchema
from Database.database import DB
from tools.convert_datetime import convert_to_beijing_time
from tools.verify_token import get_current_user

from wechatpay.wechat_pay_asyn import WechatPay

orders_router = APIRouter()
NAME_MAP = {
    'ai1': 'AI匹配1次',
    'ai3': 'AI匹配3次',
    'ai8': 'AI匹配8次',
    'one': '套餐一',
    'two': '套餐二',
    'three': '套餐三',
    'four': '套餐四',
    'five': '套餐五',
}


# 创建新订单
@orders_router.post("/createOrder")
async def createOrder(orderInfo: CreateOrderSchema, current_user_id: str = Depends(get_current_user)):
    Order_repo = DB.get_OrderSchema_repo()
    from wechatpay.wechat_pay_asyn import WechatPay
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

    # 调用创建支付函数（从WY获取支付二维码）
    wechatPay = WechatPay()
    QR_code = None

    res = await wechatPay.create_wechat_pay_QRCode(str(newOrderEntity.inserted_id),
                                                   1,
                                                   description=NAME_MAP[newOrder.package],
                                                   time_expire=convert_to_beijing_time(newOrder.expired_at)
                                                   )
    statusCode = res['code']
    message = json.loads(res['message'])

    if 200 <= int(statusCode) <= 300:
        QR_code = message['code_url']
        if QR_code:
            await Order_repo.update_one({'_id': newOrderEntity.inserted_id}, {'$set': {'QR_code': QR_code}})

        await order_manager.add_order_to_queue1(str(newOrderEntity.inserted_id), newOrder.expired_at, newOrder.package)

    return {"message": "create success", "QR_code": QR_code, 'OrderId': str(newOrderEntity.inserted_id),
            'price': newOrder.real_price, 'expired_at': newOrder.expired_at}


def get_utc_time():
    # 返回当前的 UTC 时间，带有时区信息
    return datetime.utcnow().replace(tzinfo=pytz.utc)


def ensure_utc(dt):
    """确保 datetime 对象是 'aware' 并且设置为 UTC 时区"""
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        return dt.replace(tzinfo=pytz.utc)
    return dt.astimezone(pytz.utc)


def get_remain_time(expired_at):
    """计算给定的 UTC 过期时间与当前 UTC 时间之间的剩余时间（秒）"""
    current_time = get_utc_time()  # 使用 UTC 时间
    expired_at = ensure_utc(expired_at)
    one_minute_before_expired = expired_at - timedelta(minutes=1)

    if current_time < one_minute_before_expired:
        # 如果当前时间小于过期时间前一分钟，则返回剩余秒数
        return int((one_minute_before_expired - current_time).total_seconds())
    else:
        # 否则，返回-1表示已过期或即将过期
        return -1


@orders_router.get("/getAllMyOrders")
async def getAllMyOrders(current_user_id: str = Depends(get_current_user)):
    Order_repo = DB.get_OrderSchema_repo()
    # 直接请求数据库时排序
    from pymongo import DESCENDING
    cursor = Order_repo.find({"user_id": current_user_id}).sort("created_at", DESCENDING)
    orders_data = await cursor.to_list(length=None)

    for order_data in orders_data:
        order_data['_id'] = str(order_data['_id'])
        order_data['remain_time'] = get_remain_time(order_data['expired_at'])
        if order_data['remain_time'] == -1:
            order_data['status'] = 'EXPIRED'

    if not orders_data:
        orders_data = []

    return {"status": "success", "orders": orders_data}


# 查看用户的特定订单状态
@orders_router.post("/getOneOrderStatus")
async def getOneOrderStatus(orderInfo: getOneOrderStatusSchema, current_user_id: str = Depends(get_current_user)):
    Order_repo = DB.get_OrderSchema_repo()
    order = await Order_repo.find_one({'_id': ObjectId(orderInfo.orderid)})
    if not order:
        return {"status": "fail", "message": '订单不存在'}
    if order['user_id'] != current_user_id:
        return {"status": "fail", "message": '无权限访问'}

    is_in_queue2, package = await order_manager.find_and_remove_from_queue2(orderInfo.orderid)
    order_status = OrderStatus.IN_PROGRESS if is_in_queue2 else OrderStatus.NOT_PAID
    if package in ['ai1', 'ai3', 'ai8']:
        order_status = OrderStatus.FINISHED

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


@orders_router.post("/WechatNotifyOrderStatus")
async def WechatNotifyOrderStatus(request: Request):
    try:
        headers = request.headers
        body = await request.body()
        wechatPay = WechatPay()
        res = wechatPay.wxpay.callback(headers, body)
        print(res)
        return Response(status_code=status.HTTP_200_OK)
    except Exception as e:
        # 打印错误信息，方便调试
        print(f"Error processing WeChat callback: {e}")
        return Response(status_code=status.HTTP_400_BAD_REQUEST)


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
