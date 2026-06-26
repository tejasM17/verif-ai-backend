import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Iterator

from pymongo import ASCENDING

from app.core.seed_database import get_seed_db
from app.seed.checkpoint import StageProgress
from app.seed.config import seed_config
from app.seed.generators.base import BaseGenerator
from app.seed.reference.benefits import (
    ADJECTIVES, BENEFITS, COMPANY_CULTURE_TEMPLATES, CULTURE_VALUES, INDUSTRY_PHRASES,
)
from app.seed.reference.countries import COUNTRIES
from app.seed.reference.industries import (
    COMPANY_SIZE_BUCKETS, COUNTRY_WEIGHTS, HIRING_STATUS_WEIGHTS,
    INDUSTRIES, INDUSTRY_BY_SLUG, INDUSTRY_WEIGHTS, VERIFICATION_STATUS_WEIGHTS,
)
from app.seed.reference.name_parts import generate_name
from app.seed.reference.skills import SKILLS
from app.seed.schemas import CompanyDoc
from app.seed.logger import get_logger

logger = get_logger("seed.companies")

_NS = uuid.NAMESPACE_DNS


def _slugify(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip().lower()).strip("-")
    return s[:80] or "company"


def _weighted_choice(rng, items: list, weights: list[float]):
    total = sum(weights)
    pick = rng.uniform(0, total)
    cur = 0.0
    for item, w in zip(items, weights):
        cur += w
        if pick <= cur:
            return item
    return items[-1]


class CompaniesGenerator(BaseGenerator):
    collection_name = "companies"
    schema = CompanyDoc

    SIZE_DISTRIBUTION = {
        "startup":     [0.50, 0.40, 0.08, 0.01, 0.01, 0.00, 0.00, 0.00],
        "unicorn":     [0.00, 0.05, 0.20, 0.30, 0.25, 0.15, 0.04, 0.01],
        "enterprise":  [0.00, 0.02, 0.08, 0.15, 0.15, 0.30, 0.20, 0.10],
        "software":    [0.10, 0.30, 0.30, 0.15, 0.08, 0.05, 0.01, 0.01],
        "ai":          [0.20, 0.35, 0.25, 0.10, 0.05, 0.03, 0.01, 0.01],
        "cybersecurity": [0.10, 0.30, 0.30, 0.15, 0.10, 0.04, 0.01, 0.00],
        "cloud":       [0.10, 0.25, 0.30, 0.20, 0.10, 0.04, 0.01, 0.00],
        "fintech":     [0.08, 0.25, 0.25, 0.20, 0.12, 0.07, 0.02, 0.01],
        "healthtech":  [0.15, 0.35, 0.25, 0.15, 0.05, 0.04, 0.01, 0.00],
        "edtech":      [0.20, 0.40, 0.20, 0.10, 0.05, 0.04, 0.01, 0.00],
        "ecommerce":   [0.10, 0.30, 0.25, 0.20, 0.08, 0.05, 0.01, 0.01],
        "automotive":  [0.05, 0.15, 0.20, 0.20, 0.15, 0.15, 0.05, 0.05],
        "manufacturing": [0.05, 0.15, 0.20, 0.20, 0.15, 0.15, 0.05, 0.05],
        "banking":     [0.02, 0.10, 0.15, 0.20, 0.15, 0.20, 0.10, 0.08],
        "gaming":      [0.15, 0.35, 0.25, 0.15, 0.05, 0.04, 0.01, 0.00],
        "blockchain":  [0.30, 0.45, 0.15, 0.05, 0.03, 0.01, 0.01, 0.00],
        "robotics":    [0.15, 0.35, 0.25, 0.15, 0.05, 0.04, 0.01, 0.00],
        "aerospace":   [0.05, 0.10, 0.20, 0.20, 0.15, 0.20, 0.05, 0.05],
        "telecom":     [0.02, 0.08, 0.15, 0.20, 0.15, 0.20, 0.10, 0.10],
        "government":  [0.05, 0.10, 0.15, 0.20, 0.15, 0.20, 0.10, 0.05],
    }

    def run(self) -> StageProgress:
        cfg = seed_config
        target = cfg.target_companies

        countries = [c["code"] for c in COUNTRIES]
        country_weights = [COUNTRY_WEIGHTS.get(c, 1) for c in countries]

        industry_slugs = list(INDUSTRY_WEIGHTS.keys())
        industry_weights = [INDUSTRY_WEIGHTS[s] for s in industry_slugs]

        existing_slugs = self._existing_slugs()
        logger.info("companies_existing count=%d", len(existing_slugs))

        docs = self._iter_companies(target, existing_slugs, countries, country_weights, industry_slugs, industry_weights)

        batches = max(1, (target + cfg.batch_size - 1) // cfg.batch_size)
        existing = self.checkpoint.get_stage(self.stage)
        if existing and existing.status == "completed" and existing.inserted >= target:
            return existing

        self.checkpoint.mark_running(self.stage, target, batches)
        stats = self.insert_batches(docs, target, workers=cfg.workers)
        self.checkpoint.mark_completed(self.stage)
        logger.info(
            "stage_done stage=%s inserted=%d skipped=%d failed=%d",
            self.stage, stats.inserted, stats.skipped, stats.failed,
        )
        return self.checkpoint.get_stage(self.stage)

    def _existing_slugs(self) -> set[str]:
        coll = get_seed_db()[self.collection_name]
        return {d["slug"] for d in coll.find({}, {"slug": 1})}

    def _iter_companies(
        self,
        target: int,
        existing_slugs: set[str],
        countries: list[str],
        country_weights: list[float],
        industry_slugs: list[str],
        industry_weights: list[float],
    ) -> Iterator[dict]:
        used_slugs: set[str] = set(existing_slugs)
        db = get_seed_db()
        cities = list(db["cities"].find({}, {"_id": 1, "name": 1, "country_code": 1, "country_name": 1, "state_code": 1, "state_name": 1, "timezone": 1}))
        cities_by_country: dict[str, list[dict]] = {}
        for city in cities:
            cities_by_country.setdefault(city["country_code"], []).append(city)

        now = datetime.now(timezone.utc)

        for i in range(target):
            country_code = _weighted_choice(self.rng, countries, country_weights)
            industry_slug = _weighted_choice(self.rng, industry_slugs, industry_weights)
            industry = INDUSTRY_BY_SLUG[industry_slug]

            country_cities = cities_by_country.get(country_code) or cities
            hq_city = self.rng.choice(country_cities)

            for attempt in range(50):
                name = generate_name(self.rng, region_flavor=country_code)
                slug = _slugify(f"{name}-{industry_slug}")
                if slug not in used_slugs:
                    used_slugs.add(slug)
                    break
                slug = f"{slug}-{i}-{attempt}"
                if slug not in used_slugs:
                    used_slugs.add(slug)
                    break
            else:
                slug = f"company-{uuid.uuid4().hex[:8]}"
                used_slugs.add(slug)

            size_bucket = self._size_bucket(industry_slug)
            founded_year = self._founded_year(industry_slug)

            hiring_status = _weighted_choice(
                self.rng,
                list(HIRING_STATUS_WEIGHTS.keys()),
                list(HIRING_STATUS_WEIGHTS.values()),
            )
            verification_status = _weighted_choice(
                self.rng,
                list(VERIFICATION_STATUS_WEIGHTS.keys()),
                list(VERIFICATION_STATUS_WEIGHTS.values()),
            )

            tech_stack = self._industry_tech_stack(industry_slug)
            benefits = self._pick_benefits()
            culture = self._culture(industry_slug, country_code)

            website = f"https://{slug}.com"
            linkedin = f"https://linkedin.com/company/{slug}"
            twitter = f"https://twitter.com/{slug}"
            github = f"https://github.com/{slug}" if industry_slug in {"software", "ai", "cybersecurity", "blockchain", "robotics", "startup", "unicorn"} else None

            description = self._description(industry, country_code, size_bucket)
            rating = round(self.rng.uniform(3.5, 5.0), 1)
            review_count = self.rng.randint(10, 5000)

            # Pick a default hiring role title for the runtime `role` field.
            # Mirrors the role vocabulary used by the runtime seeder and the API.
            runtime_role = self.rng.choice([
                "Software Engineer",
                "Senior Software Engineer",
                "Machine Learning Engineer",
                "Data Engineer",
                "DevOps Engineer",
                "Security Engineer",
                "Cloud Engineer",
                "Product Manager",
                "Mobile Engineer",
                "Frontend Engineer",
                "Backend Engineer",
                "Full-Stack Engineer",
            ])

            # Stable per-doc runtime uid derived from the same slug used for _id,
            # so the runtime fields and the legacy _id are 1:1 correlated.
            runtime_uid = str(uuid.uuid5(_NS, f"verifai.runtime.company.gen.{slug}"))

            yield {
                # --- Legacy / generator shape ---
                "_id": str(uuid.uuid5(_NS, f"verifai.company.{slug}")),
                "name": name,
                "slug": slug,
                "description": description,
                "industry": industry["name"],
                "industry_slug": industry_slug,
                "sub_industry": self.rng.choice(industry["sub_industries"]),
                "founded_year": founded_year,
                "company_size": size_bucket,
                "headquarters_city": hq_city["name"],
                "headquarters_state": hq_city.get("state_name"),
                "headquarters_country": hq_city["country_name"],
                "country": hq_city["country_name"],
                "country_code": country_code,
                "hq_city_id": hq_city["_id"],
                "hq_state_id": str(uuid.uuid5(_NS, f"verifai.state.{country_code}.{hq_city.get('state_code')}")) if hq_city.get("state_code") else None,
                "hq_country_id": str(uuid.uuid5(_NS, f"verifai.country.{country_code}")),
                "website": website,
                "linkedin_url": linkedin,
                "twitter_url": twitter,
                "github_url": github,
                "logo_url": f"https://logo.clearbit.com/{slug}.com",
                "cover_image_url": f"https://picsum.photos/seed/{slug}/1200/400",
                "culture": culture,
                "benefits": benefits,
                "tech_stack": tech_stack,
                "hiring_status": hiring_status,
                "verification_status": verification_status,
                "rating": rating,
                "review_count": review_count,
                "social_links": {"linkedin": linkedin, "twitter": twitter, "github": github, "website": website},
                "active_recruiters": 0,
                "active_jobs": 0,
                "tags": [industry_slug, country_code.lower(), size_bucket, hiring_status],
                "created_at": now - timedelta(days=self.rng.randint(30, 3650)),
                "updated_at": now - timedelta(days=self.rng.randint(0, 30)),
                # --- Runtime / API shape (CompanyPublic / CompanyListItem) ---
                # Mirrors the field set produced by scripts/seed_companies_runtime.py
                # so the API endpoints that read `companies` docs can resolve these
                # rows uniformly whether they came from the generator or the runtime seeder.
                "uid": runtime_uid,
                "company_name": name,
                "role": runtime_role,
                "location": f"{hq_city['name']}, {hq_city['country_name']}",
                "follower_count": 0,
                "open_roles_count": 0,
            }

    def _size_bucket(self, industry_slug: str) -> str:
        dist = self.SIZE_DISTRIBUTION.get(industry_slug, [0.10, 0.30, 0.30, 0.15, 0.08, 0.05, 0.01, 0.01])
        return _weighted_choice(self.rng, COMPANY_SIZE_BUCKETS, dist)

    def _founded_year(self, industry_slug: str) -> int:
        if industry_slug in {"startup", "unicorn", "edtech", "ai", "blockchain"}:
            return self.rng.randint(2008, 2024)
        if industry_slug in {"banking", "telecom", "aerospace", "manufacturing", "government"}:
            return self.rng.randint(1900, 2000)
        return self.rng.randint(1970, 2022)

    def _industry_tech_stack(self, industry_slug: str) -> list[str]:
        industry = INDUSTRY_BY_SLUG[industry_slug]
        relevant_categories = industry.get("tech_stack_categories", [])
        pool: list[str] = []
        for cat in relevant_categories:
            for sub_skills in SKILLS.get(cat, {}).values():
                pool.extend(sub_skills)
        if not pool:
            for sub_skills in SKILLS.get("Programming", {}).values():
                pool.extend(sub_skills)
        seen: set[str] = set()
        result: list[str] = []
        for skill in self.rng.sample(pool, k=min(len(pool), 30)):
            if skill in seen:
                continue
            seen.add(skill)
            result.append(skill)
            if len(result) >= 15:
                break
        return result

    def _pick_benefits(self) -> list[str]:
        weights = [b["weight"] for b in BENEFITS]
        picks: list[str] = []
        seen: set[str] = set()
        for _ in range(self.rng.randint(5, 10)):
            b = _weighted_choice(self.rng, BENEFITS, weights)
            if b["slug"] in seen:
                continue
            seen.add(b["slug"])
            picks.append(b["slug"])
        return picks

    def _culture(self, industry_slug: str, country_code: str) -> str:
        template = self.rng.choice(COMPANY_CULTURE_TEMPLATES)
        adj = self.rng.choice(ADJECTIVES)
        vals = self.rng.sample(CULTURE_VALUES, k=3)
        industry_phrase = self.rng.choice(INDUSTRY_PHRASES)
        geography = self.rng.choice(["multiple timezones", "the globe", "remote-first teams", "regional hubs"])
        foundation = self.rng.choice(["trust", "ownership", "craft", "customer obsession", "rigor", "speed"])
        focus = self.rng.choice(["delivering customer value", "shipping fast", "solving hard problems", "building lasting products"])
        return template.format(
            adjective=adj, value1=vals[0], value2=vals[1], value3=vals[2],
            foundation=foundation, focus=focus, geography=geography,
            industry_phrase=industry_phrase, company="our company",
        )

    def _description(self, industry: dict, country_code: str, size_bucket: str) -> str:
        sub = self.rng.choice(industry["sub_industries"])
        return (
            f"{industry['name']} company operating in the {sub} space. "
            f"Headquartered in {country_code}, with a team of {size_bucket} employees. "
            f"Focused on building best-in-class products and growing responsibly."
        )


__all__ = ["CompaniesGenerator"]
