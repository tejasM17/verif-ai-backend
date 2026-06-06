from pymongo import MongoClient, ASCENDING
from pymongo.errors import PyMongoError
from app.config.settings import settings

client: MongoClient | None = None


def get_mongodb_client() -> MongoClient:
    global client
    if client is None:
        client = MongoClient(
            settings.MONGODB_URL,
            maxPoolSize=10,
            minPoolSize=1,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
        )
    return client


def get_database():
    return get_mongodb_client()[settings.MONGODB_DATABASE]


def get_profile_images_collection():
    db = get_database()
    return db[settings.MONGODB_COLLECTION_PROFILE_IMAGES]


def ensure_indexes():
    collection = get_profile_images_collection()
    collection.create_index([("user_id", ASCENDING)], unique=True)
    collection.create_index([("firebase_uid", ASCENDING)])


def close_mongodb_connection():
    global client
    if client is not None:
        client.close()
        client = None
