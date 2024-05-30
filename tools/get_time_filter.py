# 根据筛选时间创建一个过滤器
from datetime import timedelta

from Admin.validation import DateRange


def get_time_filter(dataRange: DateRange, keyword="created_at"):
    filter_criteria = {}

    if dataRange.start_date:
        filter_criteria["$gte"] = dataRange.start_date

    if dataRange.end_date:
        filter_criteria["$lt"] = dataRange.end_date + timedelta(days=1)

    if filter_criteria:
        return {keyword: filter_criteria}
    return {}