from enum import Enum
from typing import Optional, List
from Database.PyObjectId import PyObjectId
import pytz
from bson import ObjectId
from pydantic import BaseModel, Field, root_validator
from datetime import datetime, timedelta

import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.mime.multipart import MIMEMultipart


class OrderStatus(str, Enum):
    NOT_PAID = "NOT_PAID"  # 已经创建但未付款
    EXPIRED = "EXPIRED"  # 已经过期
    IN_PROGRESS = "IN_PROGRESS"  # 已经付款 订单开始制作
    FINISHED = "FINISHED"  # 订单已经完成 （完成状态）
    RETURNING = "RETURNING"  # 订单申请退款中
    RETURNED = "RETURNED"  # 订单已经退款 （完成状态）
    RETURNFAILED = "RETURNFAILED"  # 订单退款失败


class Package(str, Enum):
    ai1 = 'ai1'
    ai3 = 'ai3'
    ai8 = 'ai8'
    one = 'one'
    two = 'two'
    three = 'three'
    four = 'four'
    five = 'five'


package_price_map = {
    'ai1': 19.99,
    'ai3': 52,
    'ai8': 128,
    'one': 24999,
    'two': 4699,
    'three': 2000,
    'four': 1000,
    'five': 2000,
}


def get_beijing_time():
    utc_dt = datetime.utcnow()  # 获取 UTC 时间
    utc_dt = utc_dt.replace(tzinfo=pytz.utc)  # 设置 UTC 时间的时区信息
    beijing_tz = pytz.timezone('Asia/Shanghai')  # 获取北京时区
    beijing_dt = utc_dt.astimezone(beijing_tz)  # 将 UTC 时间转换为北京时间
    return beijing_dt


class OrderSchema(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    created_at: datetime = Field(default_factory=get_beijing_time)
    expired_at: datetime = Field(
        default_factory=lambda: get_beijing_time() + timedelta(minutes=6))
    status: OrderStatus = OrderStatus.NOT_PAID
    package: Package
    org_price: float
    real_price: float
    discount_code: Optional[str] = None
    discount_value: Optional[float] = None
    discount_percent: Optional[float] = None
    pay_time: Optional[datetime] = None
    apply_return_time: Optional[datetime] = None
    returned_time: Optional[datetime] = None
    QR_code: str = None
    ai_total_times: Optional[int] = 0
    ai_used_times: Optional[int] = 0
    at_used_at: Optional[List[datetime]] = []

    @root_validator(pre=True)
    def set_prices_and_expired_at(cls, values):
        package = values.get('package')
        if package:
            if package in ['ai1', 'ai3', 'ai8']:
                values['ai_total_times'] = int(package[-1])

            org_price = package_price_map.get(package)
            values['org_price'] = org_price

            discount_value = values.get('discount_value')
            discount_percent = values.get('discount_percent')

            if discount_value is not None:
                values['real_price'] = org_price - discount_value
                # values['discount_percent'] = round((discount_value / org_price) * 100, 2)
            elif discount_percent is not None:
                values['real_price'] = org_price * (1 - discount_percent / 100)
                # values['discount_value'] = round(org_price * (discount_percent / 100), 2)
            else:
                values['real_price'] = org_price  # 如果没有折扣，则实际价格等于原价

        if 'created_at' in values and 'expired_at' not in values:
            values['expired_at'] = values['created_at'] + timedelta(minutes=16)
        return values

    # def check_status_change(self, new_status):
    #     if self.status == OrderStatus.NOT_PAID and new_status in [OrderStatus.FINISHED, OrderStatus.IN_PROGRESS]:
    #         sendOrder(self)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: lambda oid: str(oid),
            datetime: lambda dt: dt.isoformat(),
        }



def sendOrder(order: OrderSchema):
    from_addr = 'liudeweg@outlook.com'  # 发送邮箱地址
    to_addrs = 'deguoliuxueweg@qq.com'  # 接收邮箱地址
    password = 'Xiangyunduan2024$'  # 邮箱密码或授权码
    smtp_server = 'smtp.office365.com'

    try:
        text = f'''
        订单编号：{order['_id']}
        用户编号：{order['user_id']}
        创建时间：{order['created_at'].isoformat() if order['created_at'] else 'N/A'}
        订单内容：{order['package']}
        订单原价：{order['org_price']}
        订单实付：{order['real_price']}
        优惠码：{order['discount_code']}
        优惠比例：{order['discount_percent']}
        优惠金额：{order['discount_value']}
        付款时间：{order['pay_time'].isoformat() if order['pay_time'] else 'N/A'}
        退款时间：{order['returned_time'].isoformat() if order['returned_time'] else 'N/A'}
        AI匹配总次数：{order['ai_total_times']}
        AI匹配已使用次数：{order['ai_used_times']}
        AI匹配使用时间：{', '.join([dt.isoformat() for dt in order['at_used_at']]) if order['at_used_at'] else 'N/A'}
        '''
        msg = MIMEMultipart()
        txt = MIMEText(text, 'html', 'utf-8')
        msg.attach(txt)
        msg['From'] = Header(from_addr)
        msg['To'] = Header(to_addrs)
        msg['Subject'] = Header(f'Order Update: {order["id"]}-{order["user_id"]}')

        server = smtplib.SMTP(smtp_server, 587)  # 使用 587 端口 for TLS
        server.starttls()  # 启用 TLS
        server.login(from_addr, password)
        server.sendmail(from_addr, to_addrs, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f'Error sending email: {e}')
        return False
