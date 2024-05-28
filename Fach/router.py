import random
import re

from bson import ObjectId
from fastapi import APIRouter, HTTPException
from typing import List
from fastapi.encoders import jsonable_encoder
from Database.database import DB

fach_router = APIRouter()


@fach_router.get("/hot_universities")
async def get_hot_universities():
    Uni_Repo = DB.get_Uni_repo()
    # 构造查询条件，查找type包含'TU9'的学校
    query = {"is_tu9": "True"}

    # 从数据库中异步查询满足条件的学校
    cursor = Uni_Repo.find(query)
    result = []

    def extract_qs_rank(rank_str):
        # 正则表达式匹配包含 "QS" 和 "位" 之间的数字
        match = re.search(r"QS大学排名(\d+)位", rank_str)
        if match:
            return int(match.group(1))  # 返回匹配的数字，转换为整数
        return '-'  # 如果没有找到匹配，返回 None

    # 使用异步迭代器遍历查询结果
    async for uni in cursor:
        rank = [extract_qs_rank(rank) for rank in uni['rank'] if "QS" in rank][0]
        result.append({
            'id': str(uni['_id']),
            "name_cn": uni["name_cn"],
            "name_de": uni["name_de"],
            "rank": rank,
            "is_tu9": uni["is_tu9"],
            "is_elite": uni["is_elite"],
            'images': uni['images']
        })

    # 如果没有找到符合条件的学校，抛出异常
    if not result:
        raise HTTPException(status_code=404, detail="没有找到符合条件的学校")

    return result


@fach_router.get("/searchUni")
async def search_university(query):
    Uni_Repo = DB.get_Uni_repo()

    def extract_qs_rank(rank_str):
        # 正则表达式匹配包含 "QS" 和 "位" 之间的数字
        match = re.search(r"QS大学排名(\d+)位", rank_str)
        if match:
            return int(match.group(1))  # 返回匹配的数字，转换为整数
        return '-'  # 如果没有找到匹配，返回 None

    try:
        # 使用正则表达式来实现包含性查询
        # 注意：确保 'query' 是安全的，避免注入攻击。
        regex_query = {'$or': [
            {'name_cn': {'$regex': query, '$options': 'i'}},
            {'name_de': {'$regex': query, '$options': 'i'}}
        ]}
        cursor = Uni_Repo.find(regex_query)

        results_list = []
        async for document in cursor:
            if 'rank' in document and isinstance(document['rank'], list):
                rank_info = [extract_qs_rank(rank) for rank in document['rank'] if "QS" in rank]
                rank_qs = rank_info[0] if rank_info else None  # 防止索引错误
                document['rank'] = rank_qs

            results_list.append({k: str(v) if isinstance(v, ObjectId) else v for k, v in document.items()})

        if not results_list:
            print("No documents found for query:", query)
            return []

        return jsonable_encoder(results_list)

    except Exception as e:
        print("An error occurred:", e)
        raise HTTPException(status_code=500, detail="Internal server error")


@fach_router.get("/searchFach", response_model=List[dict])
async def search_fachs(query: str):
    Fach_Repo = DB.get_Fach_repo()
    # Uni_Repo = DB.get_Uni_repo()

    try:
        # 使用正则表达式来实现包含性查询
        # 注意：确保 'query' 是安全的，避免注入攻击。
        regex_query = {'$or': [
            {'UniName': {'$regex': query, '$options': 'i'}},
            {'name_cn': {'$regex': query, '$options': 'i'}},
            {'name_en': {'$regex': query, '$options': 'i'}},
        ]}
        cursor = Fach_Repo.find(regex_query)

        results_list = []
        async for document in cursor:
            results_list.append({k: str(v) if isinstance(v, ObjectId) else v for k, v in document.items()})
            results_list[-1]['image'] = results_list[-1]['subject_image']

        if not results_list:
            print("No documents found for query:", query)
            return []

        return jsonable_encoder(results_list)

    except Exception as e:
        print("An error occurred:", e)
        raise HTTPException(status_code=500, detail="Internal server error")


@fach_router.get("/uni/{uni_id}")
async def get_university_by_id(uni_id: str):
    Uni_Repo = DB.get_Uni_repo()
    try:
        # 将字符串ID转换为ObjectId
        uni_object_id = ObjectId(uni_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid university ID")

    # 根据ID查找学校信息
    university = await Uni_Repo.find_one({"_id": uni_object_id})

    # 如果没有找到,返回None
    if not university:
        return {'message': "查找失败"}

    university['_id'] = str(university['_id'])

    # 否则返回学校信息字典
    return university


@fach_router.get("/fach/{fach_id}")
async def get_fach_by_id(fach_id: str):
    Fach_Repo = DB.get_Fach_repo()
    try:
        # 将字符串ID转换为ObjectId
        fach_object_id = ObjectId(fach_id)

    except Exception:
        raise HTTPException(status_code=400, detail="Invalid university ID")

    # 根据ID查找学校信息
    fach = await Fach_Repo.find_one({"_id": fach_object_id})
    fach['_id'] = str(fach['_id'])
    # 如果没有找到,返回None
    if not fach:
        return {'message': "查找失败"}
    UniName = fach['UniName']

    Uni_Repo = DB.get_Uni_repo()

    cursor = Uni_Repo.find({'name_cn': UniName})
    uni = [document async for document in cursor][0]


    uni_info = {'logo': uni['logo'], 'name_cn': uni['name_cn'], 'name_de': uni['name_de'], 'is_tu9': uni['is_tu9'],
                'is_elite': uni['is_elite'],
                'images': random.sample(uni['images'], 6)}
    fach['uniInfo'] = uni_info
    # 否则返回学校信息字典
    return fach


@fach_router.get("/searchUniFach/{uni_id}")
async def search_fachs(uni_id: str, query: str):
    Fach_Repo = DB.get_Fach_repo()
    Uni_Repo = DB.get_Uni_repo()
    uni = await Uni_Repo.find_one({'_id': ObjectId(uni_id)})
    uniName = uni['name_cn']
    # uniImage = random.sample(uni['images'], 1)
    try:
        # 使用正则表达式来实现包含性查询
        # 注意：确保 'query' 是安全的，避免注入攻击。
        regex_query = {'$and': [
            {'UniName': uniName},
            {'$or': [
                {'name_cn': {'$regex': query, '$options': 'i'}},
                {'name_en': {'$regex': query, '$options': 'i'}},
            ]},

        ]}
        cursor = Fach_Repo.find(regex_query)

        results_list = []
        async for document in cursor:
            results_list.append({k: str(v) if isinstance(v, ObjectId) else v for k, v in document.items()})
            results_list[-1]['fachImage'] = results_list[-1]['subject_image']

        if not results_list:
            print("No documents found for query:", query)
            return []

        return jsonable_encoder(results_list)

    except Exception as e:
        print("An error occurred:", e)
        raise HTTPException(status_code=500, detail="Internal server error")
