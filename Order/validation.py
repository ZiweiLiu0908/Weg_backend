from pydantic import BaseModel

from Order.Schema.OrderSchema import Package


class CreateOrderSchema(BaseModel):
    discount_code: str
    package_tc: Package


class getOneOrderStatusSchema(BaseModel):
    orderid: str


class AdminRefundDecisionSchema(BaseModel):
    orderid: str
    decision: str  # "approve" or "reject"


class finishOrders(BaseModel):
    orderid: str


class refundOrders(BaseModel):
    orderid: str
    amount: str