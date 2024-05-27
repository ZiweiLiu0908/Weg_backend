import random
import string


def generate_verification_code(length=6):
    """生成指定长度的随机数字验证码"""
    return ''.join(random.choices(string.digits, k=length))
