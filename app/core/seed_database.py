from threading import Lock
from typing import Optional

from pymongo import ASCENDING, DESCENDING, GEOSPHERE, TEXT, MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import OperationFailure

from app.seed.config import SEED_COLLECTIONS, SeedConfig, seed_config
from app.seed.logger import get_logger

logger = get_logger("seed.db")

_client: Optional[MongoClient] = None
_db: Optional[Database] = None
_indexes_ready: bool = False
_lock = Lock()


def get_seed_client(config: SeedConfig | None = None) -> MongoClient:
    global _client
    cfg = config or seed_config
    if _client is None:
        with _lock:
            if _client is None:
                _client = MongoClient(
                    cfg.mongodb_uri,
                    retryWrites=True,
                    appname="verifai-seed",
                )
    return _client


def get_seed_db(config: SeedConfig | None = None) -> Database:
    global _db
    cfg = config or seed_config
    if _db is None:
        with _lock:
            if _db is None:
                _db = get_seed_client(cfg)[cfg.database_name]
    return _db


def get_seed_collection(name: str, config: SeedConfig | None = None) -> Collection:
    if name not in SEED_COLLECTIONS:
        raise ValueError(f"Unknown seed collection: {name}")
    return get_seed_db(config)[name]


def reset_clients() -> None:
    global _client, _db, _indexes_ready
    with _lock:
        if _client is not None:
            _client.close()
        _client = None
        _db = None
        _indexes_ready = False


def ensure_seed_indexes(db: Database | None = None) -> None:
    global _indexes_ready
    if _indexes_ready:
        return
    target_db = db or get_seed_db()
    with _lock:
        if _indexes_ready:
            return
        try:
            countries = target_db["countries"]
            countries.create_index([("code", ASCENDING)], unique=True, name="code_unique")
            countries.create_index([("code3", ASCENDING)], unique=True, name="code3_unique")

            states = target_db["states"]
            states.create_index(
                [("country_code", ASCENDING), ("code", ASCENDING)],
                unique=True, name="country_code_unique",
            )

            cities = target_db["cities"]
            cities.create_index(
                [("country_code", ASCENDING), ("state_code", ASCENDING), ("name", ASCENDING)],
                unique=True, name="country_state_name_unique",
            )
            cities.create_index([("country_code", ASCENDING), ("name", ASCENDING)], name="country_name_idx")

            skills = target_db["skills"]
            skills.create_index([("slug", ASCENDING)], unique=True, name="slug_unique")
            skills.create_index([("category", ASCENDING)], name="category_idx")

            companies = target_db["companies"]
            companies.create_index([("slug", ASCENDING)], unique=True, name="slug_unique")
            companies.create_index([("industry", ASCENDING)], name="industry_idx")
            companies.create_index([("country", ASCENDING), ("industry", ASCENDING)], name="country_industry_idx")
            companies.create_index([("verification_status", ASCENDING)], name="verification_idx")
            companies.create_index([("hiring_status", ASCENDING)], name="hiring_idx")
            companies.create_index([("headquarters_country", ASCENDING)], name="hq_country_idx")
            try:
                companies.create_index(
                    [("name", TEXT), ("description", TEXT), ("industry", TEXT)],
                    name="company_text_idx",
                )
            except OperationFailure:
                pass

            recruiters = target_db["recruiters"]
            recruiters.create_index([("email", ASCENDING)], unique=True, name="email_unique")
            recruiters.create_index([("firebase_uid", ASCENDING)], unique=True, sparse=True, name="firebase_uid_unique")
            recruiters.create_index([("company_id", ASCENDING)], name="company_id_idx")
            recruiters.create_index(
                [("company_id", ASCENDING), ("active_status", ASCENDING)],
                name="company_active_idx",
            )
            recruiters.create_index([("designation", ASCENDING)], name="designation_idx")
            recruiters.create_index([("country", ASCENDING)], name="country_idx")
            try:
                recruiters.create_index(
                    [("display_name", TEXT), ("bio", TEXT), ("designation", TEXT)],
                    name="recruiter_text_idx",
                )
            except OperationFailure:
                pass

            rp = target_db["recruiter_profiles"]
            rp.create_index([("recruiter_id", ASCENDING)], unique=True, name="recruiter_id_unique")
            rp.create_index([("company_id", ASCENDING)], name="profile_company_idx")

            ra = target_db["recruiter_activity"]
            ra.create_index([("recruiter_id", ASCENDING)], name="activity_recruiter_idx")
            ra.create_index([("recruiter_id", ASCENDING), ("created_at", DESCENDING)], name="activity_recent_idx")
            ra.create_index([("activity_type", ASCENDING)], name="activity_type_idx")

            rv = target_db["recruiter_verification"]
            rv.create_index([("recruiter_id", ASCENDING)], unique=True, name="verification_recruiter_unique")
            rv.create_index([("status", ASCENDING)], name="verification_status_idx")

            rpref = target_db["recruiter_preferences"]
            rpref.create_index([("recruiter_id", ASCENDING)], unique=True, name="preferences_recruiter_unique")

            rn = target_db["recruiter_notifications"]
            rn.create_index([("recruiter_id", ASCENDING)], name="notif_recruiter_idx")
            rn.create_index([("recruiter_id", ASCENDING), ("read", ASCENDING), ("created_at", DESCENDING)], name="notif_unread_idx")

            rs = target_db["recruiter_sessions"]
            rs.create_index([("session_token", ASCENDING)], unique=True, name="session_token_unique")
            rs.create_index([("recruiter_id", ASCENDING)], name="session_recruiter_idx")
            rs.create_index([("recruiter_id", ASCENDING), ("created_at", DESCENDING)], name="session_recent_idx")

            jobs = target_db["jobs"]
            jobs.create_index([("company_id", ASCENDING), ("status", ASCENDING)], name="job_company_status_idx")
            jobs.create_index([("status", ASCENDING), ("created_at", DESCENDING)], name="job_status_recent_idx")
            jobs.create_index([("recruiter_id", ASCENDING)], name="job_recruiter_idx")
            jobs.create_index([("department", ASCENDING)], name="job_department_idx")
            jobs.create_index([("work_mode", ASCENDING)], name="job_work_mode_idx")
            jobs.create_index([("employment_type", ASCENDING)], name="job_employment_idx")
            jobs.create_index([("experience_level", ASCENDING)], name="job_experience_idx")
            jobs.create_index([("country", ASCENDING)], name="job_country_idx")
            jobs.create_index([("required_skills", ASCENDING)], name="job_skills_idx")
            jobs.create_index([("category", ASCENDING)], name="job_category_idx")
            jobs.create_index([("created_at", DESCENDING)], name="job_created_idx")
            try:
                jobs.create_index(
                    [("title", TEXT), ("description", TEXT), ("department", TEXT)],
                    name="job_text_idx",
                )
            except OperationFailure:
                pass

            jc = target_db["job_categories"]
            jc.create_index([("slug", ASCENDING)], unique=True, name="jc_slug_unique")
            d = target_db["departments"]
            d.create_index([("slug", ASCENDING)], unique=True, name="dept_slug_unique")
            et = target_db["employment_types"]
            et.create_index([("slug", ASCENDING)], unique=True, name="et_slug_unique")
            el = target_db["experience_levels"]
            el.create_index([("slug", ASCENDING)], unique=True, name="el_slug_unique")
        except OperationFailure as exc:
            logger.warning("index_creation_partial error=%s", exc)

        _indexes_ready = True
        logger.info("indexes_ready collections=%d", len(SEED_COLLECTIONS))


def drop_all_seed_collections(db: Database | None = None) -> list[str]:
    target_db = db or get_seed_db()
    dropped: list[str] = []
    for name in SEED_COLLECTIONS:
        target_db.drop_collection(name)
        dropped.append(name)
    reset_clients()
    return dropped


def counts(db: Database | None = None) -> dict[str, int]:
    target_db = db or get_seed_db()
    return {name: target_db[name].estimated_document_count() for name in SEED_COLLECTIONS}


__all__ = [
    "get_seed_client", "get_seed_db", "get_seed_collection",
    "ensure_seed_indexes", "drop_all_seed_collections", "counts", "reset_clients",
]
