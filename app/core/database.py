from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.core.config import settings
import motor.motor_asyncio

class Database:
    client: AsyncIOMotorClient = None
    db = None
    resumes_bucket = None
    certificates_bucket = None

db_instance = Database()

async def init_db():
    db_instance.client = AsyncIOMotorClient(settings.MONGODB_URI)
    db_instance.db = db_instance.client[settings.MONGODB_DB_NAME]
    
    # GridFS Buckets for binary storage
    db_instance.resumes_bucket = motor.motor_asyncio.AsyncIOMotorGridFSBucket(
        db_instance.db, bucket_name="resumes"
    )
    db_instance.certificates_bucket = motor.motor_asyncio.AsyncIOMotorGridFSBucket(
        db_instance.db, bucket_name="certificates"
    )
    
    # Initialize Beanie with models (to be populated)
    await init_beanie(
        database=db_instance.db,
        document_models=[]
    )
    print(f"Connected to MongoDB: {settings.MONGODB_DB_NAME}")

async def close_db():
    if db_instance.client:
        db_instance.client.close()
