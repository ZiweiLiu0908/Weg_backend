from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, schema):
        """Custom JSON Schema for PyObjectId."""
        schema.update(type="string", format="objectid")
        return schema


# MongoDB连接配置
class Database:
    client: AsyncIOMotorClient = None

    @classmethod
    def initialize(cls, uri, db_name):
        cls.client = AsyncIOMotorClient(uri)
        cls.db = cls.client[db_name]

    @classmethod
    async def close_mongo_connection(cls):
        cls.client.close()

    @classmethod
    def get_PIN_repo(cls):
        return cls.db['PIN']

    @classmethod
    def get_User_repo(cls):
        return cls.db['User']

    @classmethod
    def get_Uni_repo(cls):
        return cls.db['Uni']

    @classmethod
    def get_Fach_repo(cls):
        return cls.db['Fach']

    @classmethod
    def get_Transcript_repo(cls):
        return cls.db['Transcript']

    @classmethod
    def get_MatchResult_repo(cls):
        return cls.db['MatchSchema']

    @classmethod
    def get_FachRecordSchema_repo(cls):
        return cls.db['FachRecordSchema']


DB = Database()