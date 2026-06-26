from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from app.core.seed_database import counts, ensure_seed_indexes
from app.seed.checkpoint import Checkpoint, StageProgress
from app.seed.config import SeedConfig, seed_config
from app.seed.firebase.bulk_auth import retry_firebase_auth, run_firebase_auth
from app.seed.generators.companies import CompaniesGenerator
from app.seed.generators.countries import (
    CitiesGenerator, CountriesGenerator, StatesGenerator,
)
from app.seed.generators.jobs import JobsGenerator
from app.seed.generators.recruiters import RecruitersGenerator
from app.seed.generators.related import (
    DepartmentsGenerator, EmploymentTypesGenerator,
    ExperienceLevelsGenerator, JobCategoriesGenerator,
)
from app.seed.generators.skills import SkillsGenerator
from app.seed.logger import get_logger

logger = get_logger("seed.orchestrator")


@dataclass
class Stage:
    name: str
    runner: Callable[[Checkpoint], StageProgress]
    required_targets: dict[str, int]


STAGES: list[Stage] = [
    Stage("countries", lambda c: CountriesGenerator(stage="countries", checkpoint=c).run(), {"countries": 14}),
    Stage("states", lambda c: StatesGenerator(stage="states", checkpoint=c).run(), {"states": 50}),
    Stage("cities", lambda c: CitiesGenerator(stage="cities", checkpoint=c).run(), {"cities": 300}),
    Stage("skills", lambda c: SkillsGenerator(stage="skills", checkpoint=c).run(), {"skills": 1000}),
    Stage("job_categories", lambda c: JobCategoriesGenerator(stage="job_categories", checkpoint=c).run(), {"job_categories": 30}),
    Stage("departments", lambda c: DepartmentsGenerator(stage="departments", checkpoint=c).run(), {"departments": 12}),
    Stage("employment_types", lambda c: EmploymentTypesGenerator(stage="employment_types", checkpoint=c).run(), {"employment_types": 5}),
    Stage("experience_levels", lambda c: ExperienceLevelsGenerator(stage="experience_levels", checkpoint=c).run(), {"experience_levels": 7}),
    Stage("companies", lambda c: CompaniesGenerator(stage="companies", checkpoint=c).run(), {"companies": 5000}),
    Stage("recruiters", lambda c: RecruitersGenerator(stage="recruiters", checkpoint=c).run(), {"recruiters": 50000}),
    Stage("jobs", lambda c: JobsGenerator(stage="jobs", checkpoint=c).run(), {"jobs": 250000}),
]

FIREBASE_STAGES = [
    Stage("firebase_auth", lambda c: run_firebase_auth(c), {}),
    Stage("firebase_auth_retry", lambda c: retry_firebase_auth(c), {}),
]


def run_full_seed(config: SeedConfig | None = None) -> dict[str, StageProgress]:
    cfg = config or seed_config
    ensure_seed_indexes()
    checkpoint = Checkpoint(cfg.checkpoint_path)

    logger.info("seed_start config=%s", cfg)
    started = datetime.now(timezone.utc)
    results: dict[str, StageProgress] = {}

    for stage in STAGES:
        if cfg.stage_filter and cfg.stage_filter != stage.name:
            logger.info("stage_skipped name=%s filter=%s", stage.name, cfg.stage_filter)
            continue
        logger.info("stage_start name=%s", stage.name)
        try:
            progress = stage.runner(checkpoint)
            results[stage.name] = progress
            from app.core.seed_database import get_seed_db
            actual_count = get_seed_db()[stage.name].count_documents({})
            if progress.inserted == 0 and actual_count > 0:
                progress.inserted = actual_count
            logger.info(
                "stage_done name=%s inserted=%d skipped=%d failed=%d status=%s",
                stage.name, progress.inserted, progress.skipped, progress.failed, progress.status,
            )
        except Exception as exc:
            logger.exception("stage_failed name=%s err=%s", stage.name, exc)
            checkpoint.mark_error(stage.name, str(exc))
            results[stage.name] = checkpoint.get_stage(stage.name)
            if cfg.stage_filter:
                raise
            continue

    if not cfg.skip_firebase and not cfg.stage_filter:
        for stage in FIREBASE_STAGES:
            try:
                progress = stage.runner(checkpoint)
                results[stage.name] = progress
            except Exception as exc:
                logger.exception("firebase_stage_failed name=%s err=%s", stage.name, exc)
                results[stage.name] = checkpoint.get_stage(stage.name)

    elapsed = (datetime.now(timezone.utc) - started).total_seconds()
    logger.info("seed_complete elapsed_sec=%.1f", elapsed)

    final_counts = counts()
    logger.info("final_counts %s", final_counts)
    return results


def resume_seed(config: SeedConfig | None = None) -> dict[str, StageProgress]:
    cfg = config or seed_config
    ensure_seed_indexes()
    checkpoint = Checkpoint(cfg.checkpoint_path)

    logger.info("seed_resume")
    results: dict[str, StageProgress] = {}

    all_stages = STAGES + ([s for s in FIREBASE_STAGES if s.name == cfg.stage_filter or not cfg.stage_filter])

    for stage in all_stages:
        existing = checkpoint.get_stage(stage.name)
        if existing and existing.status == "completed":
            results[stage.name] = existing
            continue
        try:
            progress = stage.runner(checkpoint)
            results[stage.name] = progress
        except Exception as exc:
            logger.exception("resume_failed stage=%s err=%s", stage.name, exc)
            checkpoint.mark_error(stage.name, str(exc))
            results[stage.name] = checkpoint.get_stage(stage.name)

    return results


def status_report(config: SeedConfig | None = None) -> dict:
    cfg = config or seed_config
    checkpoint = Checkpoint(cfg.checkpoint_path)
    stages = checkpoint.all_stages()
    final_counts = counts() if _safe_db() else {}
    return {
        "checkpoint_stages": {k: v.to_dict() for k, v in stages.items()},
        "collection_counts": final_counts,
    }


def _safe_db() -> bool:
    try:
        from app.core.seed_database import get_seed_db
        get_seed_db().command("ping")
        return True
    except Exception:
        return False


__all__ = ["run_full_seed", "resume_seed", "status_report", "STAGES", "FIREBASE_STAGES"]