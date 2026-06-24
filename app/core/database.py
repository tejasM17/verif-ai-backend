from pymongo import MongoClient
from app.core.config import settings

_client = None
_db = None


def get_db():
    global _client, _db
    if _db is None:
        _client = MongoClient(settings.MONGODB_URI)
        _db = _client["verifai"]
    return _db


def get_photos_collection():
    return get_db()["profile_photos"]


def get_resumes_collection():
    return get_db()["resumes"]
