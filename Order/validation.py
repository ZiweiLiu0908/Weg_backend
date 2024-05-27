from pydantic import BaseModel

from Order.Schema.OrderSchema import Package


class CreateOrderSchema(BaseModel):
    discount_code: str
    package: Package


class getOneOrderStatusSchema(BaseModel):
    orderid: str


class AdminRefundDecisionSchema(BaseModel):
    orderid: str
    decision: str  # "approve" or "reject"