from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from Order.Schema.DiscountSchema import DiscountType


class DateRange(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class CreateDiscountCode(BaseModel):
    discount_amount: float
    discount_type: DiscountType
    validity_days: int
    limit_times: int
