import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from app.core.config import settings as app_settings

SEED_DATA_DIR = Path(__file__).resolve().parents[2] / "seed_data"
SEED_DATA_DIR.mkdir(parents=True, exist_ok=True)

CHECKPOINT_PATH = SEED_DATA_DIR / "checkpoint.json"
LOG_PATH = SEED_DATA_DIR / "seed.log"
ERROR_LOG_PATH = SEED_DATA_DIR / "seed_errors.log"
CREDENTIALS_CSV_PATH = SEED_DATA_DIR / "seed_credentials.csv"

DATABASE_NAME = "verifai"

SEED_COLLECTIONS = [
    "countries",
    "states",
    "cities",
    "skills",
    "job_categories",
    "departments",
    "employment_types",
    "experience_levels",
    "companies",
    "recruiters",
    "recruiter_profiles",
    "recruiter_preferences",
    "recruiter_verification",
    "recruiter_notifications",
    "recruiter_sessions",
    "recruiter_activity",
    "jobs",
]


@dataclass
class SeedConfig:
    seed: int = 42
    workers: int = 8
    batch_size: int = 1000
    firebase_chunk_size: int = 500
    firebase_max_retries: int = 5
    firebase_initial_backoff: float = 1.0
    rtdb_mirror: bool = False

    target_companies: int = 5000
    target_recruiters: int = 50000
    target_jobs: int = 250000
    target_skills: int = 1000
    target_locations: int = 500

    rec_min_per_company: int = 5
    rec_max_per_company: int = 200

    jobs_per_company_min: int = 5
    jobs_per_company_max: int = 200

    mongodb_uri: str = ""
    database_name: str = DATABASE_NAME
    seed_data_dir: Path = SEED_DATA_DIR
    checkpoint_path: Path = CHECKPOINT_PATH
    log_path: Path = LOG_PATH
    error_log_path: Path = ERROR_LOG_PATH
    credentials_csv_path: Path = CREDENTIALS_CSV_PATH

    dry_run: bool = False
    skip_firebase: bool = False
    stage_filter: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.mongodb_uri:
            self.mongodb_uri = app_settings.MONGODB_URI


_seed_overrides: dict = {}


def apply_cli_overrides(**kwargs) -> None:
    _seed_overrides.update({k: v for k, v in kwargs.items() if v is not None})


def _build_config() -> SeedConfig:
    cfg = SeedConfig()
    for key, value in _seed_overrides.items():
        if hasattr(cfg, key):
            setattr(cfg, key, value)
    return cfg


seed_config: SeedConfig = _build_config()


def reload_config() -> SeedConfig:
    global seed_config
    new_cfg = _build_config()
    for field in SeedConfig.__dataclass_fields__:
        setattr(seed_config, field, getattr(new_cfg, field))
    return seed_config


def env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


__all__ = [
    "SeedConfig", "seed_config", "reload_config", "apply_cli_overrides",
    "SEED_DATA_DIR", "CHECKPOINT_PATH", "LOG_PATH", "ERROR_LOG_PATH",
    "CREDENTIALS_CSV_PATH", "DATABASE_NAME", "SEED_COLLECTIONS", "env_int",
]
