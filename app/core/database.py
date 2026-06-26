from pymongo import ASCENDING, DESCENDING, MongoClient, TEXT
from pymongo.collection import Collection
from pymongo.errors import OperationFailure

from app.core.config import settings

_client = None
_db = None
_indexes_ready = False


def get_db():
    global _client, _db
    if _db is None:
        _client = MongoClient(settings.MONGODB_URI)
        _db = _client["verifai"]
        _ensure_indexes(_db)
    return _db


def get_photos_collection() -> Collection:
    return get_db()["profile_photos"]


def get_resumes_collection() -> Collection:
    return get_db()["resumes"]


def get_companies_collection() -> Collection:
    return get_db()["companies"]


def get_applications_collection() -> Collection:
    return get_db()["applications"]


def get_jobs_collection() -> Collection:
    return get_db()["jobs"]


def _ensure_indexes(db):
    global _indexes_ready
    if _indexes_ready:
        return

    try:
        companies = db["companies"]
        companies.create_index([("uid", ASCENDING)], unique=True, name="uid_unique")
        companies.create_index(
            [("company_name", TEXT), ("role", TEXT), ("location", TEXT)],
            name="company_text_idx",
        )
        companies.create_index([("created_at", ASCENDING)], name="created_at_idx")
        companies.create_index(
            [("recruiter_uid", ASCENDING)],
            unique=True,
            sparse=True,
            name="recruiter_uid_unique",
        )

        applications = db["applications"]
        # Drop the legacy per-(student, company) unique index if it exists from
        # earlier seeds; we now allow one application per (student, job).
        try:
            applications.drop_index("student_company_unique")
        except OperationFailure:
            pass
        applications.create_index(
            [("student_uid", ASCENDING), ("job_uid", ASCENDING)],
            unique=True,
            name="student_job_unique",
            partialFilterExpression={"job_uid": {"$type": "string"}},
        )
        # Fallback for company-wide (no job_uid) applications: one per (student, company).
        try:
            applications.drop_index("student_company_wide_unique")
        except OperationFailure:
            pass
        applications.create_index(
            [("student_uid", ASCENDING), ("company_uid", ASCENDING)],
            unique=True,
            name="student_company_wide_unique",
            partialFilterExpression={"job_uid": None},
        )
        applications.create_index(
            [("recruiter_uid", ASCENDING), ("status", ASCENDING)],
            name="recruiter_status_idx",
        )
        applications.create_index(
            [("student_uid", ASCENDING), ("created_at", ASCENDING)],
            name="student_created_idx",
        )

        jobs = db["jobs"]
        jobs.create_index([("uid", ASCENDING)], unique=True, name="job_uid_unique")
        jobs.create_index([("company_uid", ASCENDING)], name="job_company_idx")
        jobs.create_index([("recruiter_uid", ASCENDING)], name="job_recruiter_idx")
        jobs.create_index(
            [("status", ASCENDING), ("created_at", DESCENDING)],
            name="job_status_recent_idx",
        )
    except OperationFailure:
        pass

    _indexes_ready = True