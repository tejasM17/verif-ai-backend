from datetime import datetime, timezone
from typing import Optional

from pymongo import DESCENDING

from app.core.database import get_companies_collection


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CompanyRepository:
    def _normalize(self, doc: dict | None) -> dict | None:
        if doc is None:
            return None
        doc = dict(doc)
        doc.pop("_id", None)
        return doc

    def upsert(self, uid: str, data: dict) -> dict:
        coll = get_companies_collection()
        now = _utcnow()
        set_fields = dict(data)
        set_fields["uid"] = uid
        set_fields["updated_at"] = now
        coll.update_one(
            {"uid": uid},
            {
                "$set": set_fields,
                "$setOnInsert": {
                    "created_at": now,
                    "follower_count": 0,
                    "open_roles_count": 0,
                },
            },
            upsert=True,
        )
        return self._normalize(coll.find_one({"uid": uid}))

    def get_by_uid(self, uid: str) -> dict | None:
        return self._normalize(get_companies_collection().find_one({"uid": uid}))

    def upsert_minimal(self, uid: str, recruiter_uid: str) -> dict:
        coll = get_companies_collection()
        now = _utcnow()
        coll.update_one(
            {"uid": uid},
            {
                "$setOnInsert": {
                    "uid": uid,
                    "recruiter_uid": recruiter_uid,
                    "follower_count": 0,
                    "open_roles_count": 0,
                    "created_at": now,
                    "updated_at": now,
                }
            },
            upsert=True,
        )
        return self._normalize(coll.find_one({"uid": uid}))

    def list_all(self, limit: int = 20, skip: int = 0) -> tuple[list[dict], int]:
        coll = get_companies_collection()
        cursor = (
            coll.find({}, {"uid": 1, "company_name": 1, "role": 1, "location": 1,
                           "industry": 1, "logo_url": 1})
            .sort([("created_at", DESCENDING)])
            .skip(skip)
            .limit(limit)
        )
        items = [self._normalize(d) for d in cursor]
        total = coll.count_documents({})
        return items, total

    def search(
        self,
        q: Optional[str] = None,
        location: Optional[str] = None,
        role: Optional[str] = None,
        limit: int = 20,
        skip: int = 0,
    ) -> tuple[list[dict], int]:
        coll = get_companies_collection()
        filters: dict = {}
        if location:
            filters["location"] = {"$regex": location, "$options": "i"}
        if role:
            filters["role"] = {"$regex": role, "$options": "i"}

        if q:
            text_filter = {"$text": {"$search": q}}
            combined = {**text_filter, **filters}
            cursor = (
                coll.find(
                    combined,
                    {"uid": 1, "company_name": 1, "role": 1, "location": 1,
                     "industry": 1, "logo_url": 1, "score": {"$meta": "textScore"}},
                )
                .sort([("score", {"$meta": "textScore"}), ("created_at", DESCENDING)])
                .skip(skip)
                .limit(limit)
            )
            items = [self._normalize(d) for d in cursor]
            total = coll.count_documents(combined)
            return items, total

        if not filters:
            cursor = (
                coll.find({}, {"uid": 1, "company_name": 1, "role": 1, "location": 1,
                               "industry": 1, "logo_url": 1})
                .sort([("created_at", DESCENDING)])
                .skip(skip)
                .limit(limit)
            )
            items = [self._normalize(d) for d in cursor]
            total = coll.count_documents({})
            return items, total

        cursor = (
            coll.find(filters, {"uid": 1, "company_name": 1, "role": 1, "location": 1,
                                "industry": 1, "logo_url": 1})
            .sort([("created_at", DESCENDING)])
            .skip(skip)
            .limit(limit)
        )
        items = [self._normalize(d) for d in cursor]
        total = coll.count_documents(filters)
        return items, total