from datetime import datetime, timezone, timedelta


def convert_to_beijing_time(input_datetime: str) -> str:
    # 解析输入的时间字符串
    dt = datetime.fromisoformat(str(input_datetime))

    # 创建北京时区对象
    beijing_offset = timedelta(hours=8)
    beijing_tz = timezone(beijing_offset)

    # 将输入时间转换为UTC再转换为北京时间
    dt = dt.replace(tzinfo=timezone.utc).astimezone(beijing_tz)

    # 格式化输出
    output_datetime = dt.strftime('%Y-%m-%dT%H:%M:%S%z')

    # 格式化时区部分为 `+08:00` 的形式
    output_datetime = output_datetime[:-2] + ':' + output_datetime[-2:]

    return str(output_datetime)