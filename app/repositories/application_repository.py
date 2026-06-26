from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import DESCENDING, ReturnDocument
from pymongo.errors import DuplicateKeyError

from app.core.database import get_applications_collection
from app.domain.enums.role import UserRole
from app.schemas.application import ApplicationStatus


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DuplicateApplicationError(Exception):
    pass


class ApplicationRepository:
    """Persistence for student applications.

    Uniqueness is enforced by two partial unique indexes in `_ensure_indexes`:

    - `student_job_unique` (partial, job_uid present) — a student can apply to
      a given role at most once.
    - `student_company_wide_unique` (partial, job_uid missing) — a student can
      have at most one company-wide (no job) application to any given company.

    Any `DuplicateKeyError` from Mongo is mapped to `DuplicateApplicationError`
    so the service layer can return a 409.
    """
    def _normalize(self, doc: dict | None) -> dict | None:
        if doc is None:
            return None
        doc = dict(doc)
        if "_id" in doc:
            doc["id"] = str(doc["_id"])
            doc.pop("_id", None)
        return doc

    def _to_object_id(self, app_id: str) -> ObjectId:
        try:
            return ObjectId(app_id)
        except (InvalidId, TypeError):
            raise ValueError("Invalid application id")

    def create(
        self,
        student_uid: str,
        recruiter_uid: str,
        company_uid: str,
        resume_uid: str,
        why_appoint: str,
        job_uid: Optional[str] = None,
    ) -> dict:
        coll = get_applications_collection()
        now = _utcnow()
        doc = {
            "student_uid": student_uid,
            "recruiter_uid": recruiter_uid,
            "company_uid": company_uid,
            "resume_uid": resume_uid,
            "why_appoint": why_appoint,
            "job_uid": job_uid,
            "status": ApplicationStatus.submitted.value,
            "status_history": [
                {
                    "status": ApplicationStatus.submitted.value,
                    "changed_at": now,
                    "note": None,
                }
            ],
            "created_at": now,
            "updated_at": now,
        }
        try:
            result = coll.insert_one(doc)
        except DuplicateKeyError as e:
            raise DuplicateApplicationError(str(e)) from e
        doc["_id"] = result.inserted_id
        return self._normalize(doc)

    def get_by_id(self, app_id: str) -> dict | None:
        coll = get_applications_collection()
        oid = self._to_object_id(app_id)
        return self._normalize(coll.find_one({"_id": oid}))

    def list_by_recruiter(
        self,
        recruiter_uid: str,
        status: Optional[str] = None,
        limit: int = 20,
        skip: int = 0,
    ) -> tuple[list[dict], int]:
        coll = get_applications_collection()
        filters: dict = {"recruiter_uid": recruiter_uid}
        if status:
            filters["status"] = status
        cursor = (
            coll.find(filters)
            .sort([("created_at", DESCENDING)])
            .skip(skip)
            .limit(limit)
        )
        items = [self._normalize(d) for d in cursor]
        total = coll.count_documents(filters)
        return items, total

    def list_by_student(
        self,
        student_uid: str,
        limit: int = 20,
        skip: int = 0,
    ) -> tuple[list[dict], int]:
        coll = get_applications_collection()
        filters = {"student_uid": student_uid}
        cursor = (
            coll.find(filters)
            .sort([("created_at", DESCENDING)])
            .skip(skip)
            .limit(limit)
        )
        items = [self._normalize(d) for d in cursor]
        total = coll.count_documents(filters)
        return items, total

    def update_status(
        self,
        app_id: str,
        status: ApplicationStatus,
        note: Optional[str] = None,
    ) -> dict | None:
        coll = get_applications_collection()
        oid = self._to_object_id(app_id)
        now = _utcnow()
        history_entry = {
            "status": status.value,
            "changed_at": now,
            "note": note,
        }
        result = coll.find_one_and_update(
            {"_id": oid},
            {
                "$set": {"status": status.value, "updated_at": now},
                "$push": {"status_history": history_entry},
            },
            return_document=ReturnDocument.AFTER,
        )
        return self._normalize(result)

    def delete(self, app_id: str) -> bool:
        coll = get_applications_collection()
        oid = self._to_object_id(app_id)
        result = coll.delete_one({"_id": oid})
        return result.deleted_count > 0


__all__ = [
    "ApplicationRepository",
    "DuplicateApplicationError",
    "UserRole",
]