import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from Order.Schema.OrderSchema import OrderSchema

def sendOrder(order:OrderSchema):
    from_addr = '@qq.com'#发送邮箱地址
    to_addrs=''#接收邮箱地址
    password = ''#授权码
    smtp_server = 'smtp.qq.com'
    try:
        body=f'''
订单编号：{order.id}
用户编号：{order.user_id}
创建时间：{order.created_at}
订单内容：{order.package}
订单原价：{order.org_price}
订单实付：{order.real_price}
优惠码：{order.discount_code}
优惠比例：{order.discount_percent}
优惠金额：{order.discount_value}
付款时间：{order.pay_time}
申请退款时间：{order.apply_return_time}
退款时间：{order.returned_time}
AI匹配总次数：{order.ai_total_times}
AI匹配已使用次数：{order.ai_used_times}
AI匹配使用时间：{order.at_used_at}
        '''
        title=f'{order.id}-{order.user_id}'
        smtp_server = 'smtp.office365.com'
        smtp_port = 587
        username = 'liudeweg@outlook.com'
        password = 'Xiangyunduan2024$'

        to_address='liudeweg@outlook.com'
        msg = MIMEMultipart()
        msg['From'] = username
        msg['To'] = to_address
        msg['Subject'] = title
        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # 启用TLS
        server.login(username, password)
        text = msg.as_string()
        server.sendmail(username, to_address, text)
        server.quit()
        return True
    except:
        return False