import json
from fastapi import FastAPI

from fach_recordSchema import FachRecordSchema
from database import DB

app = FastAPI()

# 初始化数据库连接
DB.initialize('mongodb://admin:Xiangyunduan2024@82.157.124.237:27017/', 'Weg')


# 异步函数来处理数据加载和数据库操作
@app.on_event("startup")
async def load_and_process_data():
    fachrecord_repo = DB.get_FachRecordSchema_repo()
    # Read the JSON file locally
    try:
        with open("path_to_your_json_file.json", "r") as file:
            data = json.load(file)
            records = []  # Validate data with Pydantic
            for item in data:
                records.append(FachRecordSchema(
                    uni_name=item['学校名称'],
                    fach_ch_name=item['专业中文名称'],
                    fach_en_name=item['专业原名称'],
                    content=item['内容']
                ))

            if records:
                new_records = [record.dict(by_alias=True) for record in records]
                await fachrecord_repo.insert_many(new_records)
                print("Data loaded and inserted into MongoDB successfully.")
            else:
                print("No valid data found to insert.")
    except Exception as e:
        print(f"Failed to load and insert data: {e}")
