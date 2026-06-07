import asyncio
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from bson import Binary
from pymongo.errors import PyMongoError

from app.database.mongodb import get_application_files_collection


class FileRepository:

    def _get_collection(self):
        return get_application_files_collection()

    async def create(
        self,
        application_id: str,
        student_id: str,
        firebase_uid: str,
        original_filename: str,
        content_type: str,
        file_size: int,
        file_type: str,
        file_data: bytes,
    ) -> Optional[dict]:
        now = datetime.now(timezone.utc)
        file_id = str(uuid4())
        storage_key = f"applications/{application_id}/{file_type}"
        doc = {
            "file_id": file_id,
            "application_id": application_id,
            "student_id": student_id,
            "firebase_uid": firebase_uid,
            "original_filename": original_filename,
            "content_type": content_type,
            "file_size": file_size,
            "storage_key": storage_key,
            "file_type": file_type,
            "file_data": Binary(file_data),
            "uploaded_at": now,
            "updated_at": now,
        }

        def _operation():
            collection = self._get_collection()
            existing = collection.find_one({
                "application_id": application_id,
                "file_type": file_type,
            })
            if existing:
                collection.update_one(
                    {"_id": existing["_id"]},
                    {"$set": {
                        "file_id": file_id,
                        "original_filename": original_filename,
                        "content_type": content_type,
                        "file_size": file_size,
                        "storage_key": storage_key,
                        "file_data": Binary(file_data),
                        "updated_at": now,
                    }},
                )
                return {**existing, **doc, "file_data": Binary(file_data)}
            else:
                result = collection.insert_one(doc)
                if result.acknowledged:
                    return doc
                return None

        try:
            return await asyncio.to_thread(_operation)
        except PyMongoError:
            return None

    async def find_by_application_and_type(
        self, application_id: str, file_type: str,
    ) -> Optional[dict]:
        def _operation():
            collection = self._get_collection()
            return collection.find_one(
                {"application_id": application_id, "file_type": file_type},
                {"_id": 0},
            )
        try:
            return await asyncio.to_thread(_operation)
        except PyMongoError:
            return None

    async def find_by_file_id(self, file_id: str) -> Optional[dict]:
        def _operation():
            collection = self._get_collection()
            return collection.find_one(
                {"file_id": file_id},
                {"_id": 0},
            )
        try:
            return await asyncio.to_thread(_operation)
        except PyMongoError:
            return None

    async def delete_by_application_and_type(
        self, application_id: str, file_type: str,
    ) -> bool:
        def _operation():
            collection = self._get_collection()
            result = collection.delete_one({
                "application_id": application_id,
                "file_type": file_type,
            })
            return result.deleted_count > 0
        try:
            return await asyncio.to_thread(_operation)
        except PyMongoError:
            return False

    async def exists_by_application_and_type(
        self, application_id: str, file_type: str,
    ) -> bool:
        def _operation():
            collection = self._get_collection()
            return collection.count_documents(
                {"application_id": application_id, "file_type": file_type},
                limit=1,
            ) > 0
        try:
            return await asyncio.to_thread(_operation)
        except PyMongoError:
            return False
