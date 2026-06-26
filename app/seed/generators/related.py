import uuid
from typing import Iterator

from app.seed.checkpoint import StageProgress
from app.seed.config import seed_config
from app.seed.generators.base import BaseGenerator
from app.seed.reference.roles import (
    DEPARTMENTS, EMPLOYMENT_TYPES, EXPERIENCE_LEVELS, JOB_CATEGORIES,
)
from app.seed.schemas import DepartmentDoc, EmploymentTypeDoc, ExperienceLevelDoc, JobCategoryDoc
from app.seed.logger import get_logger

logger = get_logger("seed.related")

_NS = uuid.NAMESPACE_DNS


class JobCategoriesGenerator(BaseGenerator):
    collection_name = "job_categories"
    schema = JobCategoryDoc

    def run(self) -> StageProgress:
        target = len(JOB_CATEGORIES)
        existing = self.checkpoint.get_stage(self.stage)
        if existing and existing.status == "completed" and existing.inserted >= target:
            return existing

        self.checkpoint.mark_running(self.stage, target, 1)
        docs = [
            {
                "_id": str(uuid.uuid5(_NS, f"verifai.job_category.{jc['slug']}")),
                "name": jc["name"],
                "slug": jc["slug"],
                "description": jc["description"],
                "display_order": i,
                "is_active": True,
            }
            for i, jc in enumerate(JOB_CATEGORIES)
        ]
        stats = self.insert_batches(iter(docs), target, workers=1)
        self.checkpoint.mark_completed(self.stage)
        logger.info("stage_done stage=%s inserted=%d", self.stage, stats.inserted)
        return self.checkpoint.get_stage(self.stage)


class DepartmentsGenerator(BaseGenerator):
    collection_name = "departments"
    schema = DepartmentDoc

    def run(self) -> StageProgress:
        target = len(DEPARTMENTS)
        existing = self.checkpoint.get_stage(self.stage)
        if existing and existing.status == "completed" and existing.inserted >= target:
            return existing

        self.checkpoint.mark_running(self.stage, target, 1)
        docs = [
            {
                "_id": str(uuid.uuid5(_NS, f"verifai.department.{d['slug']}")),
                "name": d["name"],
                "slug": d["slug"],
                "display_order": i,
                "is_active": True,
            }
            for i, d in enumerate(DEPARTMENTS)
        ]
        stats = self.insert_batches(iter(docs), target, workers=1)
        self.checkpoint.mark_completed(self.stage)
        logger.info("stage_done stage=%s inserted=%d", self.stage, stats.inserted)
        return self.checkpoint.get_stage(self.stage)


class EmploymentTypesGenerator(BaseGenerator):
    collection_name = "employment_types"
    schema = EmploymentTypeDoc

    def run(self) -> StageProgress:
        target = len(EMPLOYMENT_TYPES)
        existing = self.checkpoint.get_stage(self.stage)
        if existing and existing.status == "completed" and existing.inserted >= target:
            return existing

        self.checkpoint.mark_running(self.stage, target, 1)
        docs = [
            {
                "_id": str(uuid.uuid5(_NS, f"verifai.employment_type.{e['slug']}")),
                "name": e["name"],
                "slug": e["slug"],
                "display_order": i,
                "is_active": True,
            }
            for i, e in enumerate(EMPLOYMENT_TYPES)
        ]
        stats = self.insert_batches(iter(docs), target, workers=1)
        self.checkpoint.mark_completed(self.stage)
        logger.info("stage_done stage=%s inserted=%d", self.stage, stats.inserted)
        return self.checkpoint.get_stage(self.stage)


class ExperienceLevelsGenerator(BaseGenerator):
    collection_name = "experience_levels"
    schema = ExperienceLevelDoc

    def run(self) -> StageProgress:
        target = len(EXPERIENCE_LEVELS)
        existing = self.checkpoint.get_stage(self.stage)
        if existing and existing.status == "completed" and existing.inserted >= target:
            return existing

        self.checkpoint.mark_running(self.stage, target, 1)
        docs = [
            {
                "_id": str(uuid.uuid5(_NS, f"verifai.experience_level.{e['slug']}")),
                "name": e["name"],
                "slug": e["slug"],
                "min_years": e["min_years"],
                "max_years": e["max_years"],
                "display_order": i,
                "is_active": True,
            }
            for i, e in enumerate(EXPERIENCE_LEVELS)
        ]
        stats = self.insert_batches(iter(docs), target, workers=1)
        self.checkpoint.mark_completed(self.stage)
        logger.info("stage_done stage=%s inserted=%d", self.stage, stats.inserted)
        return self.checkpoint.get_stage(self.stage)


def run_all_related_stages(checkpoint) -> list[StageProgress]:
    out = []
    for gen_cls, stage in [
        (JobCategoriesGenerator, "job_categories"),
        (DepartmentsGenerator, "departments"),
        (EmploymentTypesGenerator, "employment_types"),
        (ExperienceLevelsGenerator, "experience_levels"),
    ]:
        gen = gen_cls(stage=stage, checkpoint=checkpoint)
        out.append(gen.run())
    return out


__all__ = [
    "JobCategoriesGenerator", "DepartmentsGenerator",
    "EmploymentTypesGenerator", "ExperienceLevelsGenerator",
    "run_all_related_stages",
]