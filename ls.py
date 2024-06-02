from datetime import datetime
import pytz

def get_beijing_time():
    utc_dt = datetime.utcnow()  # 获取 UTC 时间
    utc_dt = utc_dt.replace(tzinfo=pytz.utc)  # 设置 UTC 时间的时区信息
    beijing_tz = pytz.timezone('Asia/Shanghai')  # 获取北京时区
    beijing_dt = utc_dt.astimezone(beijing_tz)  # 将 UTC 时间转换为北京时间
    return beijing_dt
print(get_beijing_time())
