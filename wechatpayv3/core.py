# -*- coding: utf-8 -*-
import aiohttp
import json
import os
from datetime import datetime, timezone
from aiohttp import ClientTimeout
import requests

from .type import RequestType, SignType
from .utils import (aes_decrypt, build_authorization, hmac_sign,
                    load_certificate, load_private_key, rsa_decrypt,
                    rsa_encrypt, rsa_sign, rsa_verify, cryptography_version)


class Core():
    def __init__(self, mchid, cert_serial_no, private_key, apiv3_key, cert_dir=None, logger=None, proxy=None, timeout=None):
        self._proxy = proxy
        self._mchid = mchid
        self._cert_serial_no = cert_serial_no
        self._private_key = load_private_key(private_key)
        self._apiv3_key = apiv3_key
        self._gate_way = 'https://api.mch.weixin.qq.com'
        self._certificates = []
        self._cert_dir = cert_dir + '/' if cert_dir else None
        self._logger = logger
        self._timeout = ClientTimeout(sock_connect=timeout[0], sock_read=timeout[1]) if timeout else None
        self._init_certificates()
        self.session = aiohttp.ClientSession()


    async def _update_certificates(self):
        path = '/v3/certificates'
        self._certificates.clear()
        code, message = await self.request(path, skip_verify=True)
        if code != 200:
            return
        data = json.loads(message).get('data')
        for value in data:
            serial_no = value.get('serial_no')
            effective_time = value.get('effective_time')
            expire_time = value.get('expire_time')
            encrypt_certificate = value.get('encrypt_certificate')
            algorithm = nonce = associated_data = ciphertext = None
            if encrypt_certificate:
                algorithm = encrypt_certificate.get('algorithm')
                nonce = encrypt_certificate.get('nonce')
                associated_data = encrypt_certificate.get('associated_data')
                ciphertext = encrypt_certificate.get('ciphertext')
            if not (serial_no and effective_time and expire_time and algorithm and nonce and associated_data and ciphertext):
                continue
            cert_str = aes_decrypt(
                nonce=nonce,
                ciphertext=ciphertext,
                associated_data=associated_data,
                apiv3_key=self._apiv3_key)
            certificate = load_certificate(cert_str)
            if not certificate:
                continue
            if (int(cryptography_version.split(".")[0]) < 42):
                now = datetime.utcnow()
                if now < certificate.not_valid_before or now > certificate.not_valid_after:
                    continue
            else:
                now = datetime.now(timezone.utc)
                if now < certificate.not_valid_before_utc or now > certificate.not_valid_after_utc:
                    continue
            self._certificates.append(certificate)
            if not self._cert_dir:
                continue
            if not os.path.exists(self._cert_dir):
                os.makedirs(self._cert_dir)
            if not os.path.exists(self._cert_dir + serial_no + '.pem'):
                with open(self._cert_dir + serial_no + '.pem', 'w') as f:
                    f.write(cert_str)

    async def _verify_signature(self, headers, body):
        signature = headers.get('Wechatpay-Signature')
        timestamp = headers.get('Wechatpay-Timestamp')
        nonce = headers.get('Wechatpay-Nonce')
        serial_no = headers.get('Wechatpay-Serial')
        cert_found = False
        for cert in self._certificates:
            if int('0x' + serial_no, 16) == cert.serial_number:
                cert_found = True
                certificate = cert
                break
        if not cert_found:
            await self._update_certificates()
            for cert in self._certificates:
                if int('0x' + serial_no, 16) == cert.serial_number:
                    cert_found = True
                    certificate = cert
                    break
            if not cert_found:
                return False
        if not rsa_verify(timestamp, nonce, body, signature, certificate):
            return False
        return True

    async def request(self, path, method=RequestType.GET, data=None, skip_verify=False, sign_data=None, files=None, cipher_data=False, headers={}):
        if files:
            headers.update({'Content-Type': 'multipart/form-data'})
        else:
            headers.update({'Content-Type': 'application/json'})
        headers['Accept'] = 'application/json'
        headers['User-Agent'] = 'wechatpay v3 api python sdk(https://github.com/minibear2021/wechatpayv3)'

        if cipher_data:
            headers['Wechatpay-Serial'] = hex(self._last_certificate().serial_number)[2:].upper()

        authorization = build_authorization(
            path,
            method.value,
            self._mchid,
            self._cert_serial_no,
            self._private_key,
            data=sign_data if sign_data else data)
        headers['Authorization'] = authorization

        if self._logger:
            self._logger.debug(f'Request url: {self._gate_way + path}')
            self._logger.debug(f'Request type: {method.value}')
            self._logger.debug(f'Request headers: {headers}')
            self._logger.debug(f'Request params: {data}')

        url = self._gate_way + path
        async with getattr(self.session, method.value.lower())(url, headers=headers, json=data if not files else None, data=data if files else None, proxy=self._proxy, timeout=self._timeout) as response:
            response_body = await response.text()
            content_type = response.headers.get('Content-Type', '')

            if self._logger:
                self._logger.debug(f'Response status code: {response.status}')
                self._logger.debug(f'Response headers: {response.headers}')
                self._logger.debug(f'Response content: {response_body}')

            if 200 <= response.status < 300:
                # 验证签名
                if not skip_verify:
                    verified = await self._verify_signature(response.headers, response_body)
                    if not verified:
                        raise Exception('Failed to verify the signature')


                return response.status, response_body
            else:
                # 处理非 200 状态码情况
                return response.status, {'error': 'Request failed', 'status_code': response.status, 'body': response_body}


    async def close(self):
        await self.session.close()

    def sign(self, data, sign_type=SignType.RSA_SHA256):
        if sign_type == SignType.RSA_SHA256:
            sign_str = '\n'.join(data) + '\n'
            return rsa_sign(self._private_key, sign_str)
        elif sign_type == SignType.HMAC_SHA256:
            key_list = sorted(data.keys())
            sign_str = ''
            for k in key_list:
                v = data[k]
                sign_str += str(k) + '=' + str(v) + '&'
            sign_str += 'key=' + self._apiv3_key
            return hmac_sign(self._apiv3_key, sign_str)
        else:
            raise ValueError('unexpected value of sign_type.')

    def decrypt_callback(self, headers, body):
        if isinstance(body, bytes):
            body = body.decode('UTF-8')
        if self._logger:
            self._logger.debug('Callback headers: %s' % headers)
            self._logger.debug('Callback body: %s' % body)
        if not self._verify_signature(headers, body):
            return None
        data = json.loads(body)
        resource_type = data.get('resource_type')
        if resource_type != 'encrypt-resource':
            return None
        resource = data.get('resource')
        if not resource:
            return None
        algorithm = resource.get('algorithm')
        if algorithm != 'AEAD_AES_256_GCM':
            raise Exception('wechatpayv3 does not support this algorithm')
        nonce = resource.get('nonce')
        ciphertext = resource.get('ciphertext')
        associated_data = resource.get('associated_data')
        if not (nonce and ciphertext):
            return None
        if not associated_data:
            associated_data = ''
        result = aes_decrypt(
            nonce=nonce,
            ciphertext=ciphertext,
            associated_data=associated_data,
            apiv3_key=self._apiv3_key)
        if self._logger:
            self._logger.debug('Callback result: %s' % result)
        return result

    def callback(self, headers, body):
        if isinstance(body, bytes):
            body = body.decode('UTF-8')
        result = self.decrypt_callback(headers=headers, body=body)
        if result:
            data = json.loads(body)
            data.update({'resource': json.loads(result)})
            return data
        else:
            return result

    async def _init_certificates(self):
        if self._cert_dir and os.path.exists(self._cert_dir):
            for file_name in os.listdir(self._cert_dir):
                if not file_name.lower().endswith('.pem'):
                    continue
                with open(self._cert_dir + file_name, encoding="utf-8") as f:
                    certificate = load_certificate(f.read())
                if (int(cryptography_version.split(".")[0]) < 42):
                    now = datetime.utcnow()
                    if certificate and now >= certificate.not_valid_before and now <= certificate.not_valid_after:
                        self._certificates.append(certificate)
                else:
                    now = datetime.now(timezone.utc)
                    if certificate and now >= certificate.not_valid_before_utc and now <= certificate.not_valid_after_utc:
                        self._certificates.append(certificate)
        if not self._certificates:
            await self._update_certificates()
        if not self._certificates:
            raise Exception('No wechatpay platform certificate, please double check your init params.')

    def decrypt(self, ciphtext):
        return rsa_decrypt(ciphertext=ciphtext, private_key=self._private_key)

    def encrypt(self, text):
        return rsa_encrypt(text=text, certificate=self._last_certificate())

    def _last_certificate(self):
        if not self._certificates:
            self._update_certificates()
        certificate = self._certificates[0]
        for cert in self._certificates:
            if certificate.not_valid_after < cert.not_valid_after:
                certificate = cert
        return certificate
