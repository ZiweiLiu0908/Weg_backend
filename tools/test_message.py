from unisdk.sms import UniSMS
from unisdk.exception import UniException


def sendMessage(phoneNumber: str, code: str, ttl: int):
    client = UniSMS("your access key id", "your access key secret")

    try:
        # 发送短信
        res = client.send({
            "to": phoneNumber,
            "signature": "",  # 这里的签名需要去网站上弄
            "templateId": "",  # 需要创建模板
            "templateData": {  # 根据模板设计验证码和过期时间
                "code": code,
                "ttl": ttl
            }
        })
        return True
    except UniException as e:
        return False
