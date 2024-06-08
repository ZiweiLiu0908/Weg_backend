from datetime import datetime
import os
from typing import List

import pytz
from PIL import Image
import aiofiles
import io
from pypinyin import lazy_pinyin
from bson import ObjectId
from fastapi import APIRouter, File, UploadFile, Depends, HTTPException

from AI_match.Schema.MatchSchema import StatusEnum, MatchSchema
from AI_match.Schema.TranscriptSchema import Transcript
from AI_match.validation import UpdateTrans, StartMatch, getTransContetnSchema, CreateTrans, MatchResultSchema
from Database.database import DB
from tools.verify_token import get_current_user
from wy_weg.asnyc_analysis import get_structed_course_list, get_suggestion2course
from wy_weg.utils import get_file_content_as_base64

AI_match_router = APIRouter()


# 获得user的transid
@AI_match_router.get("/mytranscriptname")
async def get_transcript_name(current_user_id: str = Depends(get_current_user)):
    User_Repo = DB.get_User_repo()
    user = await User_Repo.find_one({"_id": ObjectId(current_user_id)})

    if 'transcript_ids' in user:
        trans = user['transcript_ids']

        if not trans or len(trans) == 0:
            return {"msg": "no transcript"}

        Trans_Repo = DB.get_Transcript_repo()
        data = []
        for tranid in trans:
            trans = await Trans_Repo.find_one({'_id': ObjectId(tranid)})
            data.append({'tranid': tranid, 'name': trans['name']})

        return {"msg": "Transcript obtained", 'data': data}

    else:
        return {"msg": "no transcript"}


# 根据transid获得content
@AI_match_router.post("/mytranscript_content")
async def mytranscript_content(input: getTransContetnSchema, current_user_id: str = Depends(get_current_user)):
    Trans_Repo = DB.get_Transcript_repo()
    # 将字符串类型的trans_id转换为ObjectId
    trans_object_id = ObjectId(input.trans_id)

    # 查找trans并确认存在
    trans = await Trans_Repo.find_one({"_id": trans_object_id})
    if not trans:
        raise HTTPException(status_code=404, detail="Transcript not found")

    # 确定trans属于user
    if str(trans["user_id"]) != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this transcript")

    if trans['content'] is None:
        raise HTTPException(status_code=403, detail="This transcript has no content")
    data = [[item['course_name'], item['credits'], item['grade'], item['retake'], ] for item in trans['content']]

    return {"message": "Transcript Content obtained", 'data': data}


@AI_match_router.post("/uploadTranscriptPhoto")
async def upload_transcript(
        photos: List[UploadFile] = File(...),
        current_user_id: str = Depends(get_current_user)
):
    User_repo = DB.get_User_repo()
    user = await User_repo.find_one({'_id': ObjectId(current_user_id)})
    if len(user['transcript_ids']) >= 50:
        return {"message": "Transcript uploaded failed", 'reason': '成绩单超过限制50个'}
    user_id = current_user_id
    directory = "AI_match/trans_photo"
    os.makedirs(directory, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{user_id}_{timestamp}"
    file_path = os.path.join(directory, filename)

    images = []

    for photo in photos:
        try:
            contents = await photo.read()
            image = Image.open(io.BytesIO(contents))
            images.append(image)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error processing image: {e}")

    total_width = sum(img.width for img in images)
    max_height = max(img.height for img in images)
    new_image = Image.new('RGB', (total_width, max_height))

    x_offset = 0
    for img in images:
        new_image.paste(img, (x_offset, 0))
        x_offset += img.width

    file_path_with_extension = f"{file_path}.jpg"
    new_image.save(file_path_with_extension)

    try:
        payload = "image=" + get_file_content_as_base64(file_path_with_extension, True)
        content = await get_structed_course_list(payload)
    except IOError as e:
        print(f"File could not be saved: {e}")
        raise HTTPException(status_code=500, detail="File could not be saved")
    finally:
        os.remove(file_path_with_extension)

    User_Repo = DB.get_User_repo()
    Transcript_Repo = DB.get_Transcript_repo()

    new_transcript = Transcript(
        user_id=user_id,
        content=content
    )
    result = await Transcript_Repo.insert_one(new_transcript.dict(by_alias=True))

    await User_Repo.update_one(
        {"_id": ObjectId(user_id)},
        {"$push": {"transcript_ids": str(result.inserted_id)}},
    )

    return {"message": "Transcript uploaded successfully", 'transcript_id': str(result.inserted_id)}


@AI_match_router.post("/update_trans_list")
async def update_transcript(new_trans: UpdateTrans, current_user_id: str = Depends(get_current_user)):
    Trans_Repo = DB.get_Transcript_repo()
    # 将字符串类型的trans_id转换为ObjectId
    trans_object_id = ObjectId(new_trans.trans_id)

    # 查找trans并确认存在
    trans = await Trans_Repo.find_one({"_id": trans_object_id})

    if not trans:
        raise HTTPException(status_code=404, detail="Transcript not found")

    # 确定trans属于user
    if str(trans["user_id"]) != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this transcript")

    content = [item for item in new_trans.content if any(x != "" for x in item)]
    data = []
    for item in content:
        data.append({'course_name': item[0], 'credits': item[1], 'grade': item[2], 'retake': item[3]})

    await Trans_Repo.update_one(
        {"_id": trans_object_id},
        {"$set": {"content": data}}
    )

    return {"message": "Transcript updated successfully"}


@AI_match_router.post("/manual_create_trans_list")
async def create_transcript(new_trans: CreateTrans, current_user_id: str = Depends(get_current_user)):
    Trans_Repo = DB.get_Transcript_repo()
    User_Repo = DB.get_User_repo()
    content = [item for item in new_trans.content if any(x != "" for x in item)]
    new_transcript = Transcript(
        user_id=current_user_id,
        content=content
    )
    result = await Trans_Repo.insert_one(new_transcript.dict(by_alias=True))
    await User_Repo.update_one(
        {"_id": ObjectId(current_user_id)},
        {"$push": {"transcript_ids": str(result.inserted_id)}},
    )

    return {"message": "Transcript create successfully", 'trans_id': str(result.inserted_id)}


# 根据专业id和tranid做课程匹配
@AI_match_router.post("/start_match_transcript")
async def start_match_transcript(matchInfo: StartMatch, current_user_id: str = Depends(get_current_user)):
    FachRecordSchema_repo = DB.get_FachRecordSchema_repo()  # 专业的数据库集合
    Trans_Repo = DB.get_Transcript_repo()
    User_Repo = DB.get_User_repo()
    # 检查fachid是否存在
    fach_match_record = await FachRecordSchema_repo.find_one({"_id": ObjectId(matchInfo.fach_record_id)})
    if not fach_match_record:
        raise HTTPException(status_code=404, detail="Fach not found")

    # 检查transid是否存在，并确认它属于当前用户
    trans = await Trans_Repo.find_one({"_id": ObjectId(matchInfo.trans_id), "user_id": current_user_id})
    if not trans or trans['content'] is None:
        raise HTTPException(status_code=404, detail="Transcript not found or does not belong to the current user")

    Order_repo = DB.get_OrderSchema_repo()

    query = {
        "user_id": current_user_id,
        "package": {"$in": ["ai1", "ai3", "ai8"]},
    }
    cursor = Order_repo.find(query).sort("created_at", -1)
    order_exists = False
    oldest_valid_orderid = None
    async for order in cursor:
        if order['ai_used_times'] < order['ai_total_times']:
            oldest_valid_orderid = str(order['_id'])
            order_exists = True
            break

    if not order_exists:
        return {"message": "Match failed", 'reason': "无剩余次数"}

    Match_Repo = DB.get_MatchResult_repo()

    new_Match = MatchSchema(
        user_id=current_user_id,
        trans_id=matchInfo.trans_id,
        fach_record_id=matchInfo.fach_record_id,
        uni_cn_name=fach_match_record['uni_name'],
        fach_en_cn_name=fach_match_record['fach_en_name'] + ' / ' + fach_match_record['fach_ch_name'],
    )
    result = await Match_Repo.insert_one(new_Match.dict(by_alias=True))

    content = await get_suggestion2course(trans['content'], fach_match_record['content'])

    query = {
        "user_id": current_user_id,
        "package": {"$in": ["ai1", "ai3", "ai8"]},
    }
    # earliest_order = await Order_repo.find_one(query, sort=[("created_at", 1)])
    # 获取时区为北京时间
    tz = pytz.timezone('Asia/Shanghai')
    current_time = datetime.now(tz)

    update_result = await Order_repo.update_one(
        {'_id': ObjectId(oldest_valid_orderid)},  # 查询条件
        {
            '$inc': {'ai_used_times': +1},  # ai_used_times 减少 1
            '$push': {'at_used_at': current_time}  # 在 at_used_at 添加当前时间
        }
    )



    await Match_Repo.update_one(
        {"_id": result.inserted_id},
        {"$set": {"result": content['result'], 'status': StatusEnum.已完成}}
    )
    await User_Repo.update_one(
        {"_id": ObjectId(current_user_id)},
        {"$push": {"ai_match_ids": str(result.inserted_id)}},
    )

    return {"message": "Match finished", 'ai_match_ids': str(result.inserted_id)}


@AI_match_router.get("/getAllFachRecord")
async def getAllFachRecord(current_user_id: str = Depends(get_current_user)):
    FachRecordSchema_repo = DB.get_FachRecordSchema_repo()

    projection = {"uni_name": 1, "fach_ch_name": 1, "fach_en_name": 1, "_id": 1}
    unis = []
    uni_fach_pair = {}
    fach_recordId_pair = {}
    # Cursor returned by find() with projection
    async for record in FachRecordSchema_repo.find({}, projection):

        unis.append(record['uni_name'].strip(" '()"))
        if record['uni_name'] not in uni_fach_pair:
            uni_fach_pair[record['uni_name']] = [record['fach_en_name'] + ' / ' + record['fach_ch_name']]
        else:
            uni_fach_pair[record['uni_name']].append(record['fach_en_name'] + ' / ' + record['fach_ch_name'])

        fach_recordId_pair[record['fach_en_name'] + ' / ' + record['fach_ch_name']] = str(record['_id'])
    unis = list(set(unis))
    unis = sorted(unis, key=lambda x: ''.join(lazy_pinyin(x)))

    for uni, fachs in uni_fach_pair.items():
        uni_fach_pair[uni] = sorted(fachs, key=lambda x: ''.join(lazy_pinyin(x)))
        uni_fach_pair[uni] = list(set(uni_fach_pair[uni]))

    return {"message": 'success', 'unis': unis, 'uni_fach_pair': uni_fach_pair,
            'fach_recordId_pair': fach_recordId_pair}


@AI_match_router.get("/check_ai_match_remain_times")
async def check_ai_match_remain_times(current_user_id: str = Depends(get_current_user)):
    Order_repo = DB.get_OrderSchema_repo()
    cursor = Order_repo.find({"user_id": current_user_id})
    orders_data = await cursor.to_list(length=None)
    res = 0
    # print(orders_data)
    for order_data in orders_data:
        if order_data['package'] not in ['ai1', 'ai3', 'ai8']:
            continue
        if order_data['status'] in ['NOT_PAID', 'EXPIRED']:
            continue

        res += (int(order_data['ai_total_times']) - int(order_data['ai_used_times']))
    return {'status': 'success', 'remain_times': res}


@AI_match_router.post("/check_specific_match_status")
async def check_match_status_result(recordInfo: MatchResultSchema, current_user_id: str = Depends(get_current_user)):
    Match_Repo = DB.get_MatchResult_repo()

    match = await Match_Repo.find_one({'_id': ObjectId(recordInfo.MatchResultId)})

    if match['status'] != StatusEnum.已完成:
        return {'status': match['status'], 'result': None}
    else:
        return {'status': 'finished', 'result': match['result'], 'uni_cn_name': match['uni_cn_name'],
                'fach_en_cn_name': match['fach_en_cn_name']}


@AI_match_router.get("/check_all_match")
async def check_all_match(current_user_id: str = Depends(get_current_user)):
    User_Repo = DB.get_User_repo()
    Match_Repo = DB.get_MatchResult_repo()
    user = await User_Repo.find_one({'_id': ObjectId(current_user_id)})
    match_ids = user['ai_match_ids']
    res = []
    for match_id in match_ids:
        match = await Match_Repo.find_one({'_id': ObjectId(match_id)})
        match['_id'] = str(match['_id'])
        res.append(match)

    return {"message": 'succeed', 'data': res}
