import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from app.database.session import db
from google.cloud.firestore import Transaction


def _create_document(collection: str, data: dict) -> tuple:
    doc_ref = db.collection(collection).document()
    doc_ref.set(data)
    doc = doc_ref.get()
    return doc.id, doc.to_dict()


def _get_document(collection: str, doc_id: str) -> Optional[dict]:
    doc = db.collection(collection).document(doc_id).get()
    return doc.to_dict() if doc.exists else None


def _get_document_by_field(collection: str, field: str, value: Any) -> Optional[dict]:
    docs = db.collection(collection).where(field, "==", value).limit(1).get()
    for doc in docs:
        return doc.to_dict()
    return None


def _update_document(collection: str, doc_id: str, data: dict) -> bool:
    doc_ref = db.collection(collection).document(doc_id)
    doc = doc_ref.get()
    if not doc.exists:
        return False
    doc_ref.update(data)
    return True


def _delete_document(collection: str, doc_id: str) -> bool:
    doc_ref = db.collection(collection).document(doc_id)
    doc = doc_ref.get()
    if not doc.exists:
        return False
    doc_ref.delete()
    return True


def _get_all_documents(collection: str, skip: int = 0, limit: int = 100) -> list[dict]:
    docs = db.collection(collection).offset(skip).limit(limit).get()
    return [doc.to_dict() for doc in docs]


def _count_documents(collection: str) -> int:
    return len(db.collection(collection).get())


class BaseRepository:
    collection_name: str = ""

    async def create(self, **kwargs) -> tuple[str, dict]:
        now = datetime.now(timezone.utc)
        data = {
            "id": str(uuid.uuid4()),
            **kwargs,
            "created_at": now,
            "updated_at": now,
        }
        doc_id, doc_data = await asyncio.to_thread(_create_document, self.collection_name, data)
        return doc_id, doc_data

    async def get(self, doc_id: str) -> Optional[dict]:
        return await asyncio.to_thread(_get_document, self.collection_name, doc_id)

    async def get_by_field(self, field: str, value: Any) -> Optional[dict]:
        return await asyncio.to_thread(_get_document_by_field, self.collection_name, field, value)

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[dict]:
        return await asyncio.to_thread(_get_all_documents, self.collection_name, skip, limit)

    async def update(self, doc_id: str, **kwargs) -> bool:
        data = {**kwargs, "updated_at": datetime.now(timezone.utc)}
        return await asyncio.to_thread(_update_document, self.collection_name, doc_id, data)

    async def delete(self, doc_id: str) -> bool:
        return await asyncio.to_thread(_delete_document, self.collection_name, doc_id)

    async def count(self) -> int:
        return await asyncio.to_thread(_count_documents, self.collection_name)
