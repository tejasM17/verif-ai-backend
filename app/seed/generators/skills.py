import uuid
from typing import Iterator

from app.seed.checkpoint import StageProgress
from app.seed.config import seed_config
from app.seed.generators.base import BaseGenerator
from app.seed.reference.skills import SKILLS
from app.seed.schemas import SkillDoc
from app.seed.logger import get_logger

logger = get_logger("seed.skills")

_NS = uuid.NAMESPACE_DNS


def _slugify(name: str) -> str:
    import re
    s = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip().lower()).strip("-")
    return s[:80] or "skill"


class SkillsGenerator(BaseGenerator):
    collection_name = "skills"
    schema = SkillDoc

    def run(self) -> StageProgress:
        cfg = seed_config
        target = cfg.target_skills

        docs_iter = self._iter_skills(target)
        batches = max(1, (target + cfg.batch_size - 1) // cfg.batch_size)
        existing = self.checkpoint.get_stage(self.stage)
        if existing and existing.status == "completed" and existing.inserted >= target:
            return existing

        self.checkpoint.mark_running(self.stage, target, batches)
        stats = self.insert_batches(docs_iter, target, workers=cfg.workers)
        self.checkpoint.mark_completed(self.stage)
        logger.info(
            "stage_done stage=%s inserted=%d skipped=%d failed=%d",
            self.stage, stats.inserted, stats.skipped, stats.failed,
        )
        return self.checkpoint.get_stage(self.stage)

    def _iter_skills(self, target: int) -> Iterator[dict]:
        flat: list[tuple[str, str, str]] = []
        for category, subcats in SKILLS.items():
            for subcat, items in subcats.items():
                for name in items:
                    flat.append((category, subcat, name))

        seen: set[str] = set()
        unique: list[tuple[str, str, str]] = []
        for cat, subcat, name in flat:
            slug = _slugify(name)
            if slug in seen:
                continue
            seen.add(slug)
            unique.append((cat, subcat, name))

        idx = 0
        for cat, subcat, name in unique:
            if idx >= target:
                return
            idx += 1
            slug = _slugify(name)
            related = self._related(unique, cat, idx)
            yield {
                "_id": str(uuid.uuid5(_NS, f"verifai.skill.{slug}")),
                "name": name,
                "slug": slug,
                "category": cat,
                "subcategory": subcat,
                "demand_score": round(self.rng.uniform(0.3, 1.0), 3),
                "related_skills": related,
            }

        while idx < target:
            idx += 1
            cat = self.rng.choice(list(SKILLS.keys()))
            subcat = self.rng.choice(list(SKILLS[cat].keys()))
            base = self.rng.choice(SKILLS[cat][subcat])
            suffix = self.rng.choice([
                f" {self.rng.choice(['Advanced', 'Modern', 'Production', 'Enterprise', 'Cloud', 'Distributed'])}",
                f" v{self.rng.randint(2, 9)}",
                f" for {self.rng.choice(['Cloud', 'Edge', 'AI', 'Mobile', 'Web'])}",
            ])
            name = f"{base}{suffix}"
            slug = _slugify(name)
            if slug in seen:
                slug = f"{slug}-{idx}"
            seen.add(slug)
            yield {
                "_id": str(uuid.uuid5(_NS, f"verifai.skill.{slug}")),
                "name": name,
                "slug": slug,
                "category": cat,
                "subcategory": subcat,
                "demand_score": round(self.rng.uniform(0.3, 1.0), 3),
                "related_skills": [base],
            }

    def _related(self, unique: list[tuple[str, str, str]], category: str, idx: int) -> list[str]:
        same_cat = [n for c, _, n in unique if c == category and c + "/" + n != category + "/" + unique[idx - 1][2]]
        if not same_cat:
            return []
        return self.rng.sample(same_cat, k=min(5, len(same_cat)))


__all__ = ["SkillsGenerator"]
