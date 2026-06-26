import json
import os
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Optional

from app.seed.logger import get_logger

logger = get_logger("seed.checkpoint")


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class StageProgress:
    stage: str
    status: str = "pending"
    target_count: int = 0
    completed_batches: int = 0
    total_batches: int = 0
    inserted: int = 0
    skipped: int = 0
    failed: int = 0
    last_id: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    notes: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "StageProgress":
        return cls(**{k: data.get(k) for k in cls.__dataclass_fields__ if k in data})


class Checkpoint:
    def __init__(self, path: Path):
        self.path = Path(path)
        self._lock = Lock()
        self._data: dict = {"stages": {}}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            with self.path.open("r", encoding="utf-8") as f:
                self._data = json.load(f)
            if "stages" not in self._data:
                self._data["stages"] = {}
        except json.JSONDecodeError:
            logger.warning("checkpoint_corrupt start_fresh path=%s", self.path)
            self._data = {"stages": {}}

    def _atomic_write(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(
            prefix=".checkpoint.", suffix=".tmp", dir=self.path.parent
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, sort_keys=True)
            os.replace(tmp_path, self.path)
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise

    def get_stage(self, stage: str) -> Optional[StageProgress]:
        raw = self._data.get("stages", {}).get(stage)
        if raw is None:
            return None
        return StageProgress.from_dict(raw)

    def upsert_stage(self, progress: StageProgress) -> None:
        with self._lock:
            self._data.setdefault("stages", {})[progress.stage] = progress.to_dict()
            self._atomic_write()

    def update_stage(self, stage: str, **fields) -> Optional[StageProgress]:
        with self._lock:
            raw = self._data.get("stages", {}).get(stage)
            if raw is None:
                return None
            raw.update({k: v for k, v in fields.items() if k in StageProgress.__dataclass_fields__})
            self._data["stages"][stage] = raw
            self._atomic_write()
            return StageProgress.from_dict(raw)

    def mark_running(self, stage: str, target: int, total_batches: int) -> StageProgress:
        existing = self.get_stage(stage)
        if existing and existing.status == "completed":
            return existing
        progress = StageProgress(
            stage=stage,
            status="running",
            target_count=target,
            total_batches=total_batches,
            started_at=existing.started_at if existing else _utcnow(),
        )
        self.upsert_stage(progress)
        return progress

    def mark_batch(self, stage: str, inserted: int, skipped: int, last_id: Optional[str]) -> StageProgress:
        existing = self.get_stage(stage) or StageProgress(stage=stage)
        existing.completed_batches += 1
        existing.inserted += inserted
        existing.skipped += skipped
        existing.last_id = last_id or existing.last_id
        self.upsert_stage(existing)
        return existing

    def mark_failed(self, stage: str, failed: int) -> None:
        existing = self.get_stage(stage)
        if existing is None:
            return
        existing.failed += failed
        existing.status = "running"
        self.upsert_stage(existing)

    def mark_completed(self, stage: str) -> StageProgress:
        existing = self.get_stage(stage) or StageProgress(stage=stage)
        existing.status = "completed"
        existing.finished_at = _utcnow()
        self.upsert_stage(existing)
        return existing

    def mark_error(self, stage: str, message: str) -> None:
        existing = self.get_stage(stage) or StageProgress(stage=stage)
        existing.status = "error"
        existing.notes["error"] = message
        existing.finished_at = _utcnow()
        self.upsert_stage(existing)

    def all_stages(self) -> dict[str, StageProgress]:
        return {
            name: StageProgress.from_dict(raw)
            for name, raw in self._data.get("stages", {}).items()
        }

    def reset(self) -> None:
        with self._lock:
            self._data = {"stages": {}}
            self._atomic_write()


__all__ = ["Checkpoint", "StageProgress"]
