import configparser
import logging
import os
from wechatpayv3 import WeChatPay, WeChatPayType

logging.basicConfig(filename=os.path.join(os.getcwd(), 'demo.log'), level=logging.DEBUG, filemode='a',
                    format='%(asctime)s - %(process)s - %(levelname)s: %(message)s')
LOGGER = logging.getLogger("demo")


class WechatPay:
    def __init__(self):
        self._load_wechat_pay_config()
        self.wxpay = WeChatPay(
            wechatpay_type=WeChatPayType.NATIVE,
            mchid=self.pay_config["mchid"],
            private_key=self.pay_config["private_key"],
            cert_serial_no=self.pay_config["cert_serial_no"],
            apiv3_key=self.pay_config["apiv3_key"],
            appid=self.pay_config["appid"],
            notify_url=self.pay_config["notify_url"],
            cert_dir=self.pay_config["cert_dir"],
            logger=LOGGER,
            partner_mode=self.pay_config["partner_mode"],
            proxy=self.pay_config["proxy"],
            timeout=self.pay_config["timeout"]
        )

    def _load_wechat_pay_config(self):
        config = configparser.ConfigParser()
        config.read('wechatpay/wechat_pay.ini')

        self.pay_config = {}
        private_key_path = config.get("WechatPay", "PRIVATE_KEY_PATH", fallback="")
        if not os.path.exists(private_key_path):
            raise FileNotFoundError(f"Private key file does not exist: {private_key_path}")
        with open(private_key_path) as f:
            private_key = f.read()
        self.pay_config["private_key"] = private_key
        self.pay_config["mchid"] = config.get("WechatPay", "MCH_ID")
        self.pay_config["cert_serial_no"] = config.get("WechatPay", "CERT_SERIAL_NO")
        self.pay_config["apiv3_key"] = config.get("WechatPay", "APIV3_KEY")
        self.pay_config["appid"] = config.get("WechatPay", "APP_ID")
        self.pay_config["notify_url"] = config.get("WechatPay", "NOTIFY_URL")
        self.pay_config["cert_dir"] = config.get("WechatPay", "CERT_DIR")
        self.pay_config["partner_mode"] = config.getboolean("WechatPay", "PARTNER_MODE")
        self.pay_config["proxy"] = config.get("WechatPay", "PROXY", fallback=None)
        self.pay_config["timeout"] = (10, 30)

    async def create_wechat_pay_QRCode(self, trade_no, total_fee, description,
                                       time_expire=None,
                                       ):
        """
        trade_no: str, 商户系统内部订单号，只能是数字、大小写字母_-*且在同一个商户号下唯一。
        total_fee: int, 订单总金额，单位为分。
        description: str, 商品描述
        time_expire: str, 交易结束时间，示例值:'2018-06-08T10:34:56+08:00'
        """
        code, message = await self.wxpay.pay(
            description=description,
            out_trade_no=trade_no,
            amount={'total': total_fee},
            pay_type=WeChatPayType.NATIVE,
            time_expire=time_expire,
        )

        return {'code': code, 'message': message}

    async def wy_check_order_status(self, trade_no):
        """
        trade_no: str, 商户系统内部订单号
        """
        code, message = await self.wxpay.query(
            out_trade_no=trade_no
        )
        return {'code': code, 'message': message}

    async def refund(self, trade_no, refund_no, refund_fee, total_fee, refund_desc):
        """
        trade_no: str, 商户系统内部订单号
        refund_no: str, 商户系统内部退款单号
        refund_fee: int, 退款金额
        refund_desc: str, 退款原因
        """
        code, message = await self.wxpay.refund(
            out_trade_no=trade_no,
            out_refund_no=refund_no,
            amount={'refund': refund_fee, 'total': total_fee, 'currency': 'CNY'},
            reason=refund_desc
        )
        return {'code': code, 'message': message}

    async def query_refund(self, trade_no):
        """
        trade_no: str, 商户系统内部订单号
        """
        code, message = await self.wxpay.query_refund(
            out_trade_no=trade_no
        )
        return {'code': code, 'message': message}

    async def close_order(self, trade_no):
        """
        trade_no: str, 商户系统内部订单号
        """
        code, message = await self.wxpay.close(
            out_trade_no=trade_no
        )
        return {'code': code, 'message': message}

# import asyncio
# async def main():
#     # 创建 WechatPay 实例
#     wechat_pay = WechatPay()
#
#     from random import sample
#     from string import ascii_letters, digits
#     out_trade_no = ''.join(sample(ascii_letters + digits, 8))
#     total_fee = 1                # 总费用，单位为分
#     description = '测试商品描述'    # 商品描述
#
#     # 异步调用创建 QR 码的方法
#     result = await wechat_pay.create_wechat_pay_QRCode(out_trade_no, total_fee, description)
#
#     # 输出结果
#     print(result)
#
# if __name__ == '__main__':
#     asyncio.run(main())
