import re
import configparser
import aiohttp
import requests

def all_cn_str(s:str):
    """
    判断字符串是否全为中文
    :param s: 字符串
    :return: bool
    """
    for c in s:
        if not '\u4e00' <= c <= '\u9fa5':
            return False
    return True

def has_n_cn_str(s:str,n:int):
    """
    判断字符串是否包含大于等于n个中文
    :param s: 字符串
    :param n: 中文个数
    :return: bool
    """
    count=0
    for c in s:
        if '\u4e00' <= c <= '\u9fa5':
            count+=1
    return count>=n

def is_nested_list(l):
    """
    判断是否为嵌套列表
    :param l: 列表
    :return: bool
    """
    return any(isinstance(i, list) for i in l)

def divide_long_ocr_list(ocr_result):
    """
    将长的ocr结果列表分割成多个小的ocr结果列表
    :param ocr_result: 长的ocr结果列表
    :return: 小的ocr结果列表
    """
    max_ocr_list_length=15
    divide_index=[0]
    tag=0
    for idx,ocr_res in enumerate(ocr_result):
        if has_n_cn_str(ocr_res,3):
            tag+=1
        if tag>max_ocr_list_length:
            divide_index.append(idx)
            tag=0
    divide_index.append(len(ocr_result))
    
    divide_ocr_list=[]
    for i in range(len(divide_index)-1):
        divide_ocr_list.append(ocr_result[divide_index[i]:divide_index[i+1]-1])

    return divide_ocr_list

def load_api_key(type="ocr"):
    """
    读取api_key.ini文件，获取百度AI的API_KEY和SECRET_KEY
    :return: API_KEY,SECRET_KEY
    """
    config = configparser.ConfigParser()
    config.read('api_key.ini')

    if type=="ocr":
        return '9qm6nxKKivCjvbxBg9lGlJ8V','Mq2CChMYaf9ZwdDWZhFG3UFlx5Q9ZXuu'
    elif type=="nlp":
        return 'Mjdvh1SzO5C0V0fX4iz3ibVr','N7uvDZDG5uWe7U8cLTDz5Atsjg6Tcff5'

async def async_get_access_token(api_key:str,secret_key:str):
    """
    使用 AK，SK 生成鉴权签名（Access Token）
    :return: access_token，或是None(如果错误)
    """
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {"grant_type": "client_credentials", "client_id": api_key, "client_secret": secret_key}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, params=params) as response:
            data = await response.json()
            return str(data.get("access_token"))

def get_access_token(api_key:str,secret_key:str):
    """
    使用 AK，SK 生成鉴权签名（Access Token）
    :return: access_token，或是None(如果错误)
    """
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {"grant_type": "client_credentials", "client_id": api_key, "client_secret": secret_key}
    return str(requests.post(url, params=params).json().get("access_token"))

def get_num_from_str(s:str):
    """
    从字符串中提取数字
    :param s: 字符串
    :return: 数字
    """
    match = re.search(r'-?\d+(\.\d+)?', s)
    if match:
        return float(match.group())
    else:
        return None

### For testing use only
import base64
import urllib
import re
def get_file_content_as_base64(path, urlencoded=False):
    """
    获取文件base64编码
    :param path: 文件路径
    :param urlencoded: 是否对结果进行urlencoded 
    :return: base64编码信息
    """
    with open(path, "rb") as f:
        content = base64.b64encode(f.read()).decode("utf8")
        if urlencoded:
            content = urllib.parse.quote_plus(content)
    return content

if __name__ == "__main__":
    test="-1.5abc"
    print(get_num_from_str(test))