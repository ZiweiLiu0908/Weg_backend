import aiohttp
import asyncio
import json
from wy_weg.utils import divide_long_ocr_list, load_api_key,async_get_access_token
from wy_weg.prompt import struct_course_prompt,course_suggestion_prompt,struct_course_system_prompt,course_suggestion_system_prompt

async def get_ocr_result(payload:str):
    api_key,secret_key=load_api_key()
    access_token = await async_get_access_token(api_key, secret_key)  # 使用 await 获取异步生成的 access token
    url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/accurate_basic?access_token={access_token}"

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json'
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=payload) as response:
            data = await response.text()
            if "error_code" in data:
                raise Exception("Error: ",data)

            data = json.loads(data)
            ocr_result_list=[]
            for result in data["words_result"]:
                if "words" in result:
                    ocr_result_list.append(result["words"])

            return ocr_result_list
        
async def get_course_pari_result(ocr_result:list):
    NLP_API_KEY,NLP_SECRET_KEY=load_api_key(type="nlp")

    access_token = await async_get_access_token(NLP_API_KEY, NLP_SECRET_KEY)  # 使用 await 等待访问令牌
    url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions_pro?access_token={access_token}"
    
    prompt=struct_course_prompt

    for i in ocr_result:
        prompt+=i+','
    
    payload = json.dumps({
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.01,
        "top_p": 0.8,
        "penalty_score": 1,
        "system":struct_course_system_prompt,
        "disable_search": False,
        "enable_citation": False
    })

    headers = {'Content-Type': 'application/json'}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=payload) as response:
            data = await response.text()
            if "error_code" in data:
                raise Exception("Error: ",data)
            return json.loads(data)

async def get_suggestion2course(course_list:list,major_description:str):
    NLP_API_KEY,NLP_SECRET_KEY=load_api_key(type="nlp")

    access_token = await async_get_access_token(NLP_API_KEY, NLP_SECRET_KEY)  # 使用 await 等待访问令牌
    url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions_pro?access_token={access_token}"
    
    prompt=course_suggestion_prompt

    for course in course_list:
        prompt+=course["course_name"]+','+str(course["credits"])+','+str(course["grade"])+','+str(course["retake"])+'\n'
    
    prompt+="专业描述:\n"+major_description
    payload = json.dumps({
        "messages": [
            {
                "role": "user",
                "content":prompt
            }
        ],
        "temperature": 0.2,#调低一些，保证结果的准确性
        "top_p": 0.8,
        "penalty_score": 1,
        "system":course_suggestion_system_prompt,
        "disable_search": False,
        "enable_citation": False
    })
    headers = {
        'Content-Type': 'application/json'
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=payload) as response:
            data = await response.text()
            if "error_code" in data:
                raise Exception("Error: ",data)
            return json.loads(data)

async def get_structed_course_list(payload):
    """
    这是一个整合函数，用于获取结构化的课程信息
    :param payload: base64编码的图片
    :return: 结构化的课程信息
    """
    ocr_result=await get_ocr_result(payload=payload)
    divide_ocr_result_list=divide_long_ocr_list(ocr_result)
    struct_step1_list = await asyncio.gather(
        *[get_course_pari_result(ocr_part_list) for ocr_part_list in divide_ocr_result_list]
    )
    struct_step2_list=[]
    for step1_list in struct_step1_list:
        try:
            start = step1_list["result"].find('```json') + len('```json\n')
            end = step1_list["result"].rfind('\n```')
            json_str = step1_list["result"][start:end]
            data = json.loads(json_str)
            struct_step2_list.extend(data)
        except Exception as e:
            print("step1_list:",step1_list)
    
    return struct_step2_list

### only for test
import time
from wy_weg.utils import get_file_content_as_base64

async def main():
    start_time = time.time()
    payload = "image=" + get_file_content_as_base64("4c17749d696befaef6cbdd6e860c59c.jpg", True)
    structed_course_list =await get_structed_course_list(payload)
    end_time = time.time()
    print("get_structed_course_list execution time:", end_time - start_time)
    print(structed_course_list)

    start_time = time.time()
    major_description = "这是慕尼黑工业大学的计算机科学专业，需要数学专业学分不少于20学分，计算机专业学分不少于30学分，物理专业学分不少于10学分"
    suggestion = await get_suggestion2course(structed_course_list, major_description)
    end_time = time.time()
    print("get_suggestion2course execution time:", end_time - start_time)
    print(suggestion)

if __name__ == "__main__":
    asyncio.run(main())


