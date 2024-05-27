import json
from fastapi import FastAPI

# from Fach.Schema.FachSchema import FachSchema
from UniSchema import Uni
from database import DB

app = FastAPI()

# 初始化数据库连接
DB.initialize('mongodb://admin:Xiangyunduan2024@82.157.124.237:27017/', 'Weg')
Fach_Repo = DB.get_Fach_repo()
Uni_Repo = DB.get_Uni_repo()


# 异步函数来处理数据加载和数据库操作
@app.on_event("startup")
async def load_and_process_data():
    processed = []
    fachs = Fach_Repo.find()
    async for fach in fachs:
        uni = await Uni_Repo.find_one({'name_cn': fach['UniName']})
        # if uni['name_cn'] in processed:
        #     continue
        # processed.append(uni['name_cn'])
        image = uni['images'][4] if uni and 'images' in uni else None
        if image:
            print(uni['name_cn'], image, fach['_id'])
            await Fach_Repo.update_one({'_id': fach['_id']}, {'$set': {'image': image}})
        else:
            # 如果没有找到图片，也可以选择设置一个默认值或进行其他操作
            print(f"No image found for {fach['UniName']}")



    # 打开并读取JSON文件
    # with open('./schools_info_all.json', 'r') as file:
    #     data = json.load(file)
    #
    # # 遍历JSON数据中的每一项
    # for item in data:
    #     uni_name = item['学校中文名']
    #     # 异步查询Fach信息
    #     fach_cursor = Fach_Repo.find({'UniName': uni_name}, {'_id': 1})
    #     fach_ids = await fach_cursor.to_list(None)
    #
    #     # 创建Uni实例
    #     uni = Uni(
    #         logo=item['学校图标链接'],
    #         name_cn=item['学校中文名'],
    #         name_de=item['学校德语名'],
    #         rank=item['排名'],
    #         is_tu9=str(item['是否是TU9']),
    #         is_elite=str(item['是否是精英大学']),
    #         images=item['学校照片'],
    #         offical_website=item['学校官网'],
    #         major_ids=[str(fid['_id']) for fid in fach_ids]  # 转换ObjectId为字符串
    #     )
    #     Uni_Repo.insert_one(uni.dict(by_alias=True))

# for item in data:
#     fach = FachSchema(
#         UniName=item['学校名称'][1:],
#         name_cn=item['专业中文名称'],
#         name_en=item['专业外文名称'],
#         semesterNumber=item['学期数'],
#         admission_lang=item['直接录取语言要求'],
#         cond_admission_lang=item['条件录取语言要求'],
#         language_requirement=item['语言水平要求'],
#         other_requirements=item['其它要求'],
#         is_nc=item['是否受限'],
#         instruction_lang=item['授课语言'],
#         degree=item['学位'],
#         apply_semester=item['学期时间'],
#         tuition=item['学费信息'],
#         winter_semester_apply_time=item['冬季申请时间'],
#         summer_semester_apply_time=item['夏季申请时间'],
#         subject=item['专业分类'],
#         field=item['专业方向'],
#     )
#
#     Fach_Repo.insert_one(fach.dict(by_alias=True))
