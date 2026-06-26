import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Optional, Type

from pydantic import BaseModel, ValidationError
from pymongo.collection import Collection
from pymongo.errors import BulkWriteError, OperationFailure, PyMongoError

from app.core.seed_database import get_seed_collection
from app.seed.checkpoint import Checkpoint, StageProgress
from app.seed.config import SeedConfig, seed_config
from app.seed.logger import get_error_logger, get_logger
from app.seed.progress import ProgressBar

logger = get_logger("seed.gen")
err_logger_name = "seed.errors"


@dataclass
class GeneratorStats:
    inserted: int = 0
    skipped: int = 0
    failed: int = 0
    batches: int = 0
    seconds: float = 0.0

    @property
    def rate(self) -> float:
        return self.inserted / max(self.seconds, 0.001)


class BaseGenerator:
    collection_name: str = ""
    schema: Optional[Type[BaseModel]] = None

    def __init__(
        self,
        stage: str,
        config: SeedConfig | None = None,
        checkpoint: Checkpoint | None = None,
    ):
        self.stage = stage
        self.config = config or seed_config
        self.checkpoint = checkpoint or Checkpoint(self.config.checkpoint_path)
        self.rng = random.Random(self.config.seed)
        self._stats = GeneratorStats()

    def collection(self) -> Collection:
        return get_seed_collection(self.collection_name, self.config)

    def error_logger(self):
        return get_error_logger(self.config.error_log_path)

    def run(self) -> StageProgress:
        raise NotImplementedError

    def chunked(self, items: Iterable[Any], size: int) -> Iterable[list]:
        batch: list = []
        for item in items:
            batch.append(item)
            if len(batch) >= size:
                yield batch
                batch = []
        if batch:
            yield batch

    def insert_batches(
        self,
        docs_iter: Iterable[dict],
        target_total: int,
        resume_from_id: Optional[str] = None,
        workers: int = 1,
    ) -> GeneratorStats:
        cfg = self.config
        stats = GeneratorStats()
        progress = ProgressBar(total=target_total, desc=f"{self.collection_name:<28}", unit="doc")

        batch_size = cfg.batch_size

        if resume_from_id is not None:
            logger.info(
                "stage_resume stage=%s collection=%s resume_from=%s",
                self.stage, self.collection_name, resume_from_id,
            )
            self.checkpoint.update_stage(self.stage, last_id=resume_from_id)

        resumed = resume_from_id is None

        if workers <= 1:
            batches = self._batched(docs_iter, batch_size)
            for batch in batches:
                if not resumed:
                    last = self.checkpoint.get_stage(self.stage)
                    last_id = last.last_id if last else None
                    if last_id is None or self._batch_contains_id(batch, last_id):
                        resumed = True
                    else:
                        stats.skipped += len(batch)
                        stats.batches += 1
                        last_id = batch[-1].get("_id") if batch else None
                        self.checkpoint.mark_batch(self.stage, 0, len(batch), last_id)
                        continue
                inserted, skipped, failed = self._insert_one_batch(batch)
                stats.inserted += inserted
                stats.skipped += skipped
                stats.failed += failed
                stats.batches += 1
                progress.update(inserted)
                last_id = batch[-1].get("_id") if batch else None
                self.checkpoint.mark_batch(self.stage, inserted, skipped, last_id)
            progress.close()
            self._stats = stats
            return stats

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = []
            for batch in self._batched(docs_iter, batch_size):
                if not resumed:
                    last = self.checkpoint.get_stage(self.stage)
                    last_id = last.last_id if last else None
                    if last_id is None or self._batch_contains_id(batch, last_id):
                        resumed = True
                    else:
                        stats.skipped += len(batch)
                        stats.batches += 1
                        last_id = batch[-1].get("_id") if batch else None
                        self.checkpoint.mark_batch(self.stage, 0, len(batch), last_id)
                        continue
                futures.append(pool.submit(self._insert_one_batch, batch))

            for fut in as_completed(futures):
                inserted, skipped, failed = fut.result()
                stats.inserted += inserted
                stats.skipped += skipped
                stats.failed += failed
                stats.batches += 1
                progress.update(inserted)

        progress.close()
        self._stats = stats
        return stats

    def _batched(self, items: Iterable[Any], size: int) -> Iterable[list]:
        batch: list = []
        for item in items:
            batch.append(item)
            if len(batch) >= size:
                yield batch
                batch = []
        if batch:
            yield batch

    def _batch_contains_id(self, batch: list[dict], last_id: str) -> bool:
        if not batch:
            return False
        return any(d.get("_id") == last_id for d in batch)

    def _insert_one_batch(self, batch: list[dict]) -> tuple[int, int, int]:
        if not batch:
            return (0, 0, 0)

        skipped = 0
        if self.schema is not None:
            valid: list[dict] = []
            for doc in batch:
                try:
                    model = self.schema.model_validate(doc)
                    valid.append(model.to_mongo())
                except ValidationError as exc:
                    skipped += 1
                    self.error_logger().error(
                        "schema_validation_failed collection=%s id=%s err=%s",
                        self.collection_name, doc.get("_id"), exc.errors(),
                    )
            batch = valid

        if not batch:
            return (0, skipped, 0)

        coll = self.collection()
        last_exc: Optional[Exception] = None
        for attempt in range(5):
            try:
                result = coll.insert_many(batch, ordered=False)
                inserted = len(result.inserted_ids)
                return (inserted, skipped, 0)
            except BulkWriteError as exc:
                details = exc.details or {}
                write_errors = details.get("writeErrors", [])
                dup_count = sum(1 for e in write_errors if e.get("code") == 11000)
                non_dup = [e for e in write_errors if e.get("code") != 11000]
                if non_dup:
                    self.error_logger().error(
                        "bulk_write_errors collection=%s non_dup=%d dup=%d err=%s",
                        self.collection_name, len(non_dup), dup_count, non_dup[:3],
                    )
                inserted = len(batch) - len(write_errors)
                return (inserted, dup_count, len(non_dup))
            except OperationFailure as exc:
                last_exc = exc
                if exc.code in (7, 6, 89, 91, 9001):
                    sleep_s = min(2 ** attempt, 30)
                    logger.warning(
                        "transient_mongo_error collection=%s code=%s attempt=%d sleep=%.1fs",
                        self.collection_name, exc.code, attempt, sleep_s,
                    )
                    time.sleep(sleep_s)
                    continue
                self.error_logger().error(
                    "mongo_op_failure collection=%s err=%s", self.collection_name, exc,
                )
                return (0, 0, len(batch))
            except PyMongoError as exc:
                last_exc = exc
                sleep_s = min(2 ** attempt, 30)
                logger.warning(
                    "pymongo_error collection=%s attempt=%d sleep=%.1fs err=%s",
                    self.collection_name, attempt, sleep_s, exc,
                )
                time.sleep(sleep_s)
                continue

        self.error_logger().error(
            "insert_batch_giving_up collection=%s err=%s",
            self.collection_name, last_exc,
        )
        return (0, 0, len(batch))

    def validate_doc(self, doc: dict) -> dict:
        if self.schema is None:
            return doc
        model = self.schema.model_validate(doc)
        return model.to_mongo()


__all__ = ["BaseGenerator", "GeneratorStats"]
