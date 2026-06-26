import asyncio
import uuid
from datetime import datetime, timezone
from typing import Optional

from pymongo import DESCENDING

from app.core.database import get_companies_collection, get_jobs_collection


_NS = uuid.NAMESPACE_DNS


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _count_open_sync(company_uid: str) -> int:
    return get_jobs_collection().count_documents(
        {"company_uid": company_uid, "status": "open"}
    )


def _apply_open_roles_count_sync(company_uid: str, count: int) -> None:
    get_companies_collection().update_one(
        {"uid": company_uid},
        {"$set": {"open_roles_count": count, "updated_at": _utcnow()}},
    )


async def _bump_open_roles_count(company_uid: str | None) -> None:
    """Recompute and persist `open_roles_count` on the parent company doc.

    Two round-trips run in the threadpool (not on the event loop) — blocking
    I/O is offloaded, but count + update are sequential because the second
    write depends on the first read. Safe to call with a missing company
    (no-op).
    """
    if not company_uid:
        return
    count = await asyncio.to_thread(_count_open_sync, company_uid)
    await asyncio.to_thread(_apply_open_roles_count_sync, company_uid, count)


class JobRepository:
    def _normalize(self, doc: dict | None) -> dict | None:
        if doc is None:
            return None
        doc = dict(doc)
        doc.pop("_id", None)
        return doc

    async def create(self, recruiter_uid: str, company_uid: str, data: dict) -> dict:
        def _do() -> dict:
            coll = get_jobs_collection()
            uid = str(uuid.uuid5(_NS, f"verifai.job.{company_uid}.{uuid.uuid4().hex}"))
            now = _utcnow()
            doc = {
                "uid": uid,
                "company_uid": company_uid,
                "recruiter_uid": recruiter_uid,
                **data,
                "status": data.get("status", "open"),
                "required_skills": data.get("required_skills", []),
                "created_at": now,
                "updated_at": now,
            }
            coll.insert_one(doc)
            return doc

        doc = await asyncio.to_thread(_do)
        await _bump_open_roles_count(company_uid)
        return self._normalize(doc)

    async def get_by_uid(self, uid: str) -> dict | None:
        return await asyncio.to_thread(self._get_by_uid_sync, uid)

    def _get_by_uid_sync(self, uid: str) -> dict | None:
        return self._normalize(get_jobs_collection().find_one({"uid": uid}))

    async def list_by_company(
        self,
        company_uid: str,
        status: Optional[str] = None,
        limit: int = 50,
        skip: int = 0,
    ) -> tuple[list[dict], int]:
        return await asyncio.to_thread(
            self._list_by_company_sync, company_uid, status, limit, skip
        )

    def _list_by_company_sync(
        self,
        company_uid: str,
        status: Optional[str],
        limit: int,
        skip: int,
    ) -> tuple[list[dict], int]:
        coll = get_jobs_collection()
        filters = {"company_uid": company_uid}
        if status:
            filters["status"] = status
        cursor = coll.find(filters).sort([("created_at", DESCENDING)]).skip(skip).limit(limit)
        items = [self._normalize(d) for d in cursor]
        total = coll.count_documents(filters)
        return items, total

    async def list_by_recruiter(
        self,
        recruiter_uid: str,
        status: Optional[str] = None,
        limit: int = 50,
        skip: int = 0,
    ) -> tuple[list[dict], int]:
        return await asyncio.to_thread(
            self._list_by_recruiter_sync, recruiter_uid, status, limit, skip
        )

    def _list_by_recruiter_sync(
        self,
        recruiter_uid: str,
        status: Optional[str],
        limit: int,
        skip: int,
    ) -> tuple[list[dict], int]:
        coll = get_jobs_collection()
        filters = {"recruiter_uid": recruiter_uid}
        if status:
            filters["status"] = status
        cursor = coll.find(filters).sort([("created_at", DESCENDING)]).skip(skip).limit(limit)
        items = [self._normalize(d) for d in cursor]
        total = coll.count_documents(filters)
        return items, total

    async def update(self, uid: str, data: dict) -> dict | None:
        def _do() -> dict | None:
            coll = get_jobs_collection()
            data["updated_at"] = _utcnow()
            coll.update_one({"uid": uid}, {"$set": data})
            return self._get_by_uid_sync(uid)

        updated = await asyncio.to_thread(_do)
        if updated:
            await _bump_open_roles_count(updated.get("company_uid"))
        return updated

    async def delete(self, uid: str) -> bool:
        def _do() -> tuple[bool, str | None]:
            coll = get_jobs_collection()
            existing = coll.find_one({"uid": uid}, {"company_uid": 1})
            if not existing:
                return False, None
            result = coll.delete_one({"uid": uid})
            return result.deleted_count > 0, existing.get("company_uid")

        deleted, company_uid = await asyncio.to_thread(_do)
        if deleted and company_uid:
            await _bump_open_roles_count(company_uid)
        return deleted

    async def count_open_for_company(self, company_uid: str) -> int:
        return await asyncio.to_thread(self._count_open_sync, company_uid)

    def _count_open_sync(self, company_uid: str) -> int:
        return get_jobs_collection().count_documents(
            {"company_uid": company_uid, "status": "open"}
        )


__all__ = ["JobRepository"]