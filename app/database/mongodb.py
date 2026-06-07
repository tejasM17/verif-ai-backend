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


def get_application_files_collection():
    db = get_database()
    return db[settings.MONGODB_COLLECTION_APPLICATION_FILES]


def get_audit_logs_collection():
    db = get_database()
    return db[settings.MONGODB_COLLECTION_AUDIT_LOGS]


def ensure_indexes():
    profile_collection = get_profile_images_collection()
    profile_collection.create_index([("user_id", ASCENDING)], unique=True)
    profile_collection.create_index([("firebase_uid", ASCENDING)])

    files_collection = get_application_files_collection()
    files_collection.create_index([("application_id", ASCENDING), ("file_type", ASCENDING)], unique=True)
    files_collection.create_index([("file_id", ASCENDING)], unique=True)
    files_collection.create_index([("student_id", ASCENDING)])
    files_collection.create_index([("firebase_uid", ASCENDING)])

    audit_collection = get_audit_logs_collection()
    audit_collection.create_index([("application_id", ASCENDING)])
    audit_collection.create_index([("actor_id", ASCENDING)])
    audit_collection.create_index([("timestamp", ASCENDING)])
    audit_collection.create_index([("action", ASCENDING)])


def close_mongodb_connection():
    global client
    if client is not None:
        client.close()
        client = None
