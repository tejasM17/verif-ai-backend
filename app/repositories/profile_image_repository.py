import asyncio
from datetime import datetime, timezone
from typing import Optional

from bson import Binary
from pymongo.errors import PyMongoError

from app.database.mongodb import get_profile_images_collection


class ProfileImageRepository:

    def _get_collection(self):
        return get_profile_images_collection()

    async def upsert(
        self,
        user_id: str,
        firebase_uid: str,
        filename: str,
        content_type: str,
        file_size: int,
        image_data: bytes,
    ) -> bool:
        now = datetime.now(timezone.utc)
        doc = {
            "user_id": user_id,
            "firebase_uid": firebase_uid,
            "filename": filename,
            "content_type": content_type,
            "file_size": file_size,
            "image_data": Binary(image_data),
            "created_at": now,
            "updated_at": now,
        }

        def _operation():
            collection = self._get_collection()
            existing = collection.find_one({"user_id": user_id})
            if existing:
                collection.update_one(
                    {"user_id": user_id},
                    {"$set": {
                        "firebase_uid": firebase_uid,
                        "filename": filename,
                        "content_type": content_type,
                        "file_size": file_size,
                        "image_data": Binary(image_data),
                        "updated_at": now,
                    }},
                )
                return True
            else:
                result = collection.insert_one(doc)
                return result.acknowledged

        try:
            return await asyncio.to_thread(_operation)
        except PyMongoError:
            return False

    async def find_by_user_id(self, user_id: str) -> Optional[dict]:
        def _operation():
            collection = self._get_collection()
            doc = collection.find_one(
                {"user_id": user_id},
                {"_id": 0, "image_data": 1, "content_type": 1, "filename": 1, "file_size": 1},
            )
            return doc

        try:
            return await asyncio.to_thread(_operation)
        except PyMongoError:
            return None

    async def find_by_firebase_uid(self, firebase_uid: str) -> Optional[dict]:
        def _operation():
            collection = self._get_collection()
            doc = collection.find_one(
                {"firebase_uid": firebase_uid},
                {"_id": 0, "image_data": 1, "content_type": 1, "filename": 1, "file_size": 1},
            )
            return doc

        try:
            return await asyncio.to_thread(_operation)
        except PyMongoError:
            return None

    async def delete_by_user_id(self, user_id: str) -> bool:
        def _operation():
            collection = self._get_collection()
            result = collection.delete_one({"user_id": user_id})
            return result.deleted_count > 0

        try:
            return await asyncio.to_thread(_operation)
        except PyMongoError:
            return False

    async def exists_by_user_id(self, user_id: str) -> bool:
        def _operation():
            collection = self._get_collection()
            return collection.count_documents({"user_id": user_id}, limit=1) > 0

        try:
            return await asyncio.to_thread(_operation)
        except PyMongoError:
            return False
