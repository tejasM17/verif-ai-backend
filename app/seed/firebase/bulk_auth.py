import csv
import secrets
import string
import time
from dataclasses import dataclass
from typing import Iterator, Optional

from firebase_admin import auth, exceptions

from app.core.config import init_firebase
from app.seed.checkpoint import Checkpoint, StageProgress
from app.seed.config import SeedConfig, seed_config
from app.seed.logger import get_logger

logger = get_logger("seed.firebase")


@dataclass
class ImportResult:
    created: int = 0
    existing: int = 0
    failed: int = 0
    skipped: int = 0

    @property
    def total(self) -> int:
        return self.created + self.existing + self.failed + self.skipped


@dataclass
class ImportRecord:
    uid: str
    email: str
    password: str
    display_name: str
    photo_url: Optional[str] = None


def generate_password(length: int = 16) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*-_=+"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def init_admin() -> None:
    try:
        init_firebase()
    except ValueError:
        pass


class BulkAuthImporter:
    def __init__(
        self,
        config: SeedConfig | None = None,
        checkpoint: Checkpoint | None = None,
    ):
        self.config = config or seed_config
        self.checkpoint = checkpoint or Checkpoint(self.config.checkpoint_path)

    def run(self) -> StageProgress:
        from app.core.seed_database import get_seed_db

        stage = "firebase_auth"
        target_stage = self.checkpoint.get_stage(stage)
        if target_stage and target_stage.status == "completed" and target_stage.inserted >= 0:
            logger.info("firebase_skip_completed inserted=%d", target_stage.inserted)
            return target_stage

        init_admin()

        db = get_seed_db()
        recruiters = db["recruiters"]
        pending = list(recruiters.find({"firebase_sync_status": {"$in": ["pending", None]}}, {"_id": 1, "email": 1, "display_name": 1, "photo_url": 1, "company_id": 1}))

        logger.info("firebase_pending count=%d", len(pending))
        target = len(pending)
        self.checkpoint.mark_running(stage, target, max(1, target // self.config.firebase_chunk_size))

        credentials_path = self.config.credentials_csv_path
        credentials_path.parent.mkdir(parents=True, exist_ok=True)

        write_header = not credentials_path.exists() or credentials_path.stat().st_size == 0
        creds_file = credentials_path.open("a", encoding="utf-8", newline="")
        creds_writer = csv.writer(creds_file)
        if write_header:
            creds_writer.writerow(["recruiter_id", "email", "password", "display_name", "company_id"])

        result = ImportResult()
        chunk: list[ImportRecord] = []

        def flush() -> None:
            nonlocal chunk
            if not chunk:
                return
            chunk_result = self._import_chunk(chunk)
            for rec, outcome in zip(chunk, chunk_result):
                if outcome == "created":
                    recruiters.update_one(
                        {"_id": rec.uid},
                        {"$set": {"firebase_uid": rec.uid, "firebase_sync_status": "synced"}},
                    )
                    creds_writer.writerow([rec.uid, rec.email, rec.password, rec.display_name, ""])
                    result.created += 1
                elif outcome == "existing":
                    recruiters.update_one(
                        {"_id": rec.uid},
                        {"$set": {"firebase_uid": rec.uid, "firebase_sync_status": "synced"}},
                    )
                    creds_writer.writerow([rec.uid, rec.email, rec.password, rec.display_name, ""])
                    result.existing += 1
                elif outcome == "failed_quota":
                    result.skipped += 1
                else:
                    result.failed += 1

            self.checkpoint.mark_batch(stage, len(chunk), 0, chunk[-1].uid)
            chunk = []

        for r in pending:
            password = generate_password()
            rec = ImportRecord(
                uid=r["_id"],
                email=r["email"],
                password=password,
                display_name=r.get("display_name", ""),
                photo_url=r.get("photo_url"),
            )
            chunk.append(rec)
            if len(chunk) >= self.config.firebase_chunk_size:
                flush()

        flush()
        creds_file.close()

        self.checkpoint.mark_completed(stage)
        logger.info(
            "firebase_summary created=%d existing=%d skipped=%d failed=%d total=%d",
            result.created, result.existing, result.skipped, result.failed, result.total,
        )
        return self.checkpoint.get_stage(stage)

    def _import_chunk(self, records: list[ImportRecord]) -> list[str]:
        backoff = self.config.firebase_initial_backoff
        last_exc: Optional[Exception] = None
        for attempt in range(self.config.firebase_max_retries):
            try:
                users = [
                    auth.ImportUserRecord(
                        uid=r.uid,
                        email=r.email,
                        password=r.password,
                        display_name=r.display_name,
                        photo_url=r.photo_url,
                    )
                    for r in records
                ]
                auth.import_users(users, hash_algo=auth.UserImportHash.BCRYPT)
                return ["created"] * len(records)
            except exceptions.FirebaseError as exc:
                last_exc = exc
                if self._is_quota_error(exc):
                    logger.warning("firebase_quota_error err=%s", exc)
                    return ["failed_quota"] * len(records)
                if attempt < self.config.firebase_max_retries - 1:
                    logger.warning(
                        "firebase_transient_error attempt=%d sleep=%.1fs err=%s",
                        attempt, backoff, exc,
                    )
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                logger.error("firebase_error err=%s", exc)
                return ["failed"] * len(records)
            except Exception as exc:
                last_exc = exc
                if self._is_quota_error(exc):
                    logger.warning("firebase_quota_error err=%s", exc)
                    return ["failed_quota"] * len(records)
                if attempt < self.config.firebase_max_retries - 1:
                    logger.warning(
                        "firebase_transient_error attempt=%d sleep=%.1fs err=%s",
                        attempt, backoff, exc,
                    )
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                logger.error("firebase_unexpected_error err=%s", exc)
                return ["failed"] * len(records)
        logger.error("firebase_chunk_failed_after_retries err=%s", last_exc)
        return ["failed"] * len(records)

    def _is_quota_error(self, exc: Exception) -> bool:
        msg = str(exc).lower()
        return any(token in msg for token in ("quota", "rate limit", "too many requests", "auth/quota-exceeded"))

    def retry_failed(self) -> StageProgress:
        from app.core.seed_database import get_seed_db

        stage = "firebase_auth_retry"
        init_admin()
        db = get_seed_db()
        recruiters = db["recruiters"]
        pending = list(recruiters.find({"firebase_sync_status": "pending"}, {"_id": 1, "email": 1, "display_name": 1, "photo_url": 1}))
        logger.info("firebase_retry count=%d", len(pending))
        target = len(pending)
        self.checkpoint.mark_running(stage, target, max(1, target // self.config.firebase_chunk_size))

        credentials_path = self.config.credentials_csv_path
        creds_writer = csv.writer(credentials_path.open("a", encoding="utf-8", newline=""))
        result = ImportResult()
        chunk: list[ImportRecord] = []

        def flush() -> None:
            nonlocal chunk
            if not chunk:
                return
            outcome = self._import_chunk(chunk)
            for rec, status in zip(chunk, outcome):
                if status == "created":
                    recruiters.update_one({"_id": rec.uid}, {"$set": {"firebase_uid": rec.uid, "firebase_sync_status": "synced"}})
                    creds_writer.writerow([rec.uid, rec.email, rec.password, rec.display_name, ""])
                    result.created += 1
                elif status == "existing":
                    recruiters.update_one({"_id": rec.uid}, {"$set": {"firebase_uid": rec.uid, "firebase_sync_status": "synced"}})
                    creds_writer.writerow([rec.uid, rec.email, rec.password, rec.display_name, ""])
                    result.existing += 1
                elif status == "failed_quota":
                    result.skipped += 1
                else:
                    result.failed += 1
            self.checkpoint.mark_batch(stage, len(chunk), 0, chunk[-1].uid)
            chunk = []

        for r in pending:
            chunk.append(ImportRecord(uid=r["_id"], email=r["email"], password=generate_password(), display_name=r.get("display_name", ""), photo_url=r.get("photo_url")))
            if len(chunk) >= self.config.firebase_chunk_size:
                flush()
        flush()
        creds_writer.writerow([])
        self.checkpoint.mark_completed(stage)
        logger.info("firebase_retry_summary created=%d existing=%d skipped=%d failed=%d", result.created, result.existing, result.skipped, result.failed)
        return self.checkpoint.get_stage(stage)


def run_firebase_auth(checkpoint: Checkpoint | None = None) -> StageProgress:
    importer = BulkAuthImporter(checkpoint=checkpoint)
    return importer.run()


def retry_firebase_auth(checkpoint: Checkpoint | None = None) -> StageProgress:
    importer = BulkAuthImporter(checkpoint=checkpoint)
    return importer.retry_failed()


__all__ = ["BulkAuthImporter", "ImportRecord", "ImportResult", "run_firebase_auth", "retry_firebase_auth"]