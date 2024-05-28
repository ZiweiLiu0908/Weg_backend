from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DateRange(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None