from datetime import datetime, timezone, timedelta


def is_first_before_second_beijing(time1: datetime, time2: datetime) -> bool:
    # 定义北京时区
    beijing_tz = timezone(timedelta(hours=8))

    # 如果第一个时间没有时区信息，假设它是 UTC 时间
    if time1.tzinfo is None:
        time1 = time1.replace(tzinfo=timezone.utc)
    else:
        # 如果第一个时间有时区信息，先转换为 UTC
        time1 = time1.astimezone(timezone.utc)

    # 如果第二个时间没有时区信息，假设它是 UTC 时间
    if time2.tzinfo is None:
        time2 = time2.replace(tzinfo=timezone.utc)
    else:
        # 如果第二个时间有时区信息，先转换为 UTC
        time2 = time2.astimezone(timezone.utc)

    # 将两个时间都转换为北京时区
    time1_beijing = time1.astimezone(beijing_tz)
    time2_beijing = time2.astimezone(beijing_tz)

    # 比较两个北京时区的时间
    return time1_beijing < time2_beijing