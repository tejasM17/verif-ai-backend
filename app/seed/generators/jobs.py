import uuid
from datetime import datetime, timedelta, timezone
from typing import Iterator

from app.core.seed_database import get_seed_db
from app.seed.checkpoint import StageProgress
from app.seed.config import seed_config
from app.seed.generators.base import BaseGenerator
from app.seed.reference.countries import COUNTRIES
from app.seed.reference.industries import INDUSTRY_BY_SLUG
from app.seed.reference.roles import (
    DEPARTMENTS, EDUCATION_LEVELS, EMPLOYMENT_TYPES, EXPERIENCE_LEVELS,
    JOB_CATEGORIES, JOB_STATUSES, SENIORITY_LEVELS, WORK_MODES,
)
from app.seed.reference.salaries import (
    BASE_SALARY_USD, COUNTRY_PURCHASING_POWER, CURRENCY_BASE_USD,
    DEPARTMENT_SALARY_MULTIPLIER, INDUSTRY_SALARY_MULTIPLIER,
)
from app.seed.reference.skills import SKILLS
from app.seed.schemas import JobDoc
from app.seed.logger import get_logger

logger = get_logger("seed.jobs")

_NS = uuid.NAMESPACE_DNS


def _weighted_choice(rng, items, weights):
    total = sum(weights)
    pick = rng.uniform(0, total)
    cur = 0.0
    for item, w in zip(items, weights):
        cur += w
        if pick <= cur:
            return item
    return items[-1]


JOB_DESCRIPTION_TEMPLATES = [
    "We're looking for a {level} {role_title} to join our {department} team. You will work on {focus_area} alongside a world-class engineering team.",
    "Join our {department} team as a {level} {role_title}. You'll help us build the next generation of {focus_area}.",
    "As a {level} {role_title}, you will design and implement solutions that power {focus_area} for our customers worldwide.",
    "We're hiring a {level} {role_title} to lead {focus_area} initiatives and drive technical excellence across the team.",
]

RESPONSIBILITY_TEMPLATES = [
    "Design and implement {tech} solutions that scale to millions of users",
    "Collaborate with cross-functional teams including Product, Design and Data",
    "Mentor junior engineers and contribute to engineering best practices",
    "Participate in code reviews, design discussions and architectural decisions",
    "Build and maintain robust, well-tested production systems",
    "Identify and resolve performance bottlenecks and reliability issues",
    "Contribute to the team's engineering culture and hiring efforts",
    "Drive continuous improvement in our development and deployment processes",
]

REQUIREMENT_TEMPLATES = [
    "{years}+ years of experience in {tech} or related technologies",
    "Strong foundation in computer science fundamentals (data structures, algorithms, distributed systems)",
    "Experience building production-grade systems at scale",
    "Excellent problem-solving and communication skills",
    "Track record of delivering high-quality, well-tested code",
    "Experience with cloud platforms such as AWS, GCP or Azure",
    "Bachelor's or Master's degree in Computer Science or equivalent practical experience",
    "Experience working in agile, fast-paced environments",
    "Strong sense of ownership and ability to work independently",
    "Familiarity with modern CI/CD pipelines and DevOps practices",
]

NICE_TO_HAVE_TEMPLATES = [
    "Open source contributions",
    "Experience with {tech}",
    "Publications in top-tier conferences",
    "Experience leading technical projects from inception to launch",
    "Familiarity with our tech stack: {tech}",
]

FOCUS_AREAS = [
    "distributed systems", "real-time analytics", "machine learning platforms", "developer tools",
    "data pipelines", "cloud infrastructure", "mobile applications", "security tooling",
    "search and discovery", "personalization", "recommendation systems", "fraud detection",
    "payment processing", "customer experience", "internal tooling", "growth experiments",
    "embedded systems", "computer vision", "natural language processing", "blockchain protocols",
]


class JobsGenerator(BaseGenerator):
    collection_name = "jobs"
    schema = JobDoc

    def run(self) -> StageProgress:
        cfg = seed_config
        target = cfg.target_jobs

        companies = self._load_companies()
        recruiters_by_company = self._load_recruiters()
        skills_pool = self._load_skills_pool()
        if not companies:
            self.checkpoint.mark_error(self.stage, "no companies")
            return self.checkpoint.get_stage(self.stage)
        if not recruiters_by_company:
            self.checkpoint.mark_error(self.stage, "no recruiters")
            return self.checkpoint.get_stage(self.stage)

        per_company = self._allocate_jobs(companies, recruiters_by_company, target)
        existing = self.checkpoint.get_stage(self.stage)
        if existing and existing.status == "completed" and existing.inserted >= target:
            return existing

        batches = max(1, (target + cfg.batch_size - 1) // cfg.batch_size)
        self.checkpoint.mark_running(self.stage, target, batches)

        stats = self._dispatch_jobs(per_company, skills_pool)

        self.checkpoint.mark_completed(self.stage)
        logger.info("stage_done stage=%s inserted=%d skipped=%d failed=%d",
                    self.stage, stats["inserted"], stats["skipped"], stats["failed"])
        return self.checkpoint.get_stage(self.stage)

    def _load_companies(self) -> list[dict]:
        coll = get_seed_db()["companies"]
        return list(coll.find({}, {
            "_id": 1, "slug": 1, "name": 1, "industry_slug": 1,
            "country_code": 1, "country": 1, "tech_stack": 1, "benefits": 1,
            "headquarters_city": 1, "headquarters_state": 1,
            "company_size": 1, "hiring_status": 1,
        }))

    def _load_recruiters(self) -> dict[str, list[dict]]:
        coll = get_seed_db()["recruiters"]
        out: dict[str, list[dict]] = {}
        for r in coll.find({}, {"_id": 1, "company_id": 1, "firebase_uid": 1, "display_name": 1}):
            out.setdefault(r["company_id"], []).append(r)
        return out

    def _load_skills_pool(self) -> list[str]:
        skills_coll = get_seed_db()["skills"]
        return [d["name"] for d in skills_coll.find({}, {"name": 1})]

    def _allocate_jobs(self, companies, recruiters_by_company, target):
        result = {}
        total_recruiters = sum(len(v) for v in recruiters_by_company.values())
        if total_recruiters == 0:
            return {}
        avg_jobs_per_recruiter = target / total_recruiters
        running = 0
        for c in companies:
            c_recs = len(recruiters_by_company.get(c["_id"], []))
            if c_recs == 0:
                continue
            company_jobs = max(
                cfg_min := seed_config.jobs_per_company_min,
                min(seed_config.jobs_per_company_max, int(c_recs * avg_jobs_per_recruiter * self.rng.uniform(0.7, 1.3))),
            )
            if c.get("hiring_status") == "closed":
                company_jobs = max(1, company_jobs // 5)
            elif c.get("hiring_status") == "limited":
                company_jobs = max(2, company_jobs // 2)
            result[c["_id"]] = company_jobs
            running += company_jobs
        if running > target:
            scale = target / running
            result = {k: max(1, int(v * scale)) for k, v in result.items()}
        return result

    def _dispatch_jobs(self, per_company, skills_pool) -> dict:
        db = get_seed_db()
        coll = db["jobs"]
        stats = {"inserted": 0, "skipped": 0, "failed": 0}

        buf = seed_config.batch_size
        batch: list[dict] = []
        running_total = 0

        def flush() -> None:
            nonlocal batch
            if not batch:
                return
            valid = []
            for doc in batch:
                try:
                    valid.append(JobDoc.model_validate(doc).to_mongo())
                except Exception as exc:
                    self.error_logger().error("schema_validation_failed id=%s err=%s", doc.get("_id"), exc)
                    stats["failed"] += 1
            try:
                coll.insert_many(valid, ordered=False)
                stats["inserted"] += len(valid)
                last = valid[-1]["_id"] if valid else None
                self.checkpoint.mark_batch(self.stage, len(valid), 0, last)
            except Exception as exc:
                from pymongo.errors import BulkWriteError
                if isinstance(exc, BulkWriteError):
                    details = exc.details or {}
                    errs = details.get("writeErrors", [])
                    dup = sum(1 for e in errs if e.get("code") == 11000)
                    non_dup = len(errs) - dup
                    stats["inserted"] += max(0, len(valid) - len(errs))
                    stats["skipped"] += dup
                    stats["failed"] += non_dup
                    if non_dup:
                        self.error_logger().error("bulk_write_errors jobs non_dup=%d dup=%d", non_dup, dup)
                else:
                    self.error_logger().error("mongo_error jobs err=%s", exc)
                    stats["failed"] += len(valid)
            batch = []

        for company in self._load_companies():
            count = per_company.get(company["_id"], 0)
            if count == 0:
                continue
            recruiters = self._load_recruiters().get(company["_id"], [])
            if not recruiters:
                continue

            industry = INDUSTRY_BY_SLUG.get(company.get("industry_slug"), INDUSTRY_BY_SLUG["software"])
            roles_pool = list(industry.get("common_roles", ["Software Engineer"]))
            skills_pool_industry = company.get("tech_stack") or skills_pool[:30]

            for i in range(count):
                rec = self.rng.choice(recruiters)
                job = self._build_job(company, rec, roles_pool, skills_pool_industry)
                batch.append(job)
                running_total += 1
                if len(batch) >= buf:
                    flush()
        flush()

        return stats

    def _build_job(self, company, rec, roles_pool, skills_pool) -> dict:
        seniority = _weighted_choice(
            self.rng,
            [s["slug"] for s in SENIORITY_LEVELS],
            [s["weight"] for s in SENIORITY_LEVELS],
        )
        seniority_meta = next(s for s in SENIORITY_LEVELS if s["slug"] == seniority)

        base_role = self.rng.choice(roles_pool)
        if seniority in ("intern",):
            title = f"Intern {base_role}"
        elif seniority in ("junior", "mid", "senior"):
            title = f"{seniority_meta['name']} {base_role}"
        elif seniority in ("lead", "staff", "principal"):
            title = f"{seniority_meta['name']} {base_role}"
        else:
            title = f"{base_role} ({seniority_meta['name']})"

        seniority_to_experience = {
            "intern": "entry", "junior": "junior", "mid": "mid", "senior": "senior",
            "lead": "lead", "staff": "lead", "principal": "principal",
            "manager": "lead", "director": "principal", "vp": "executive",
        }
        experience_level = seniority_to_experience.get(seniority, "mid")
        experience_level_meta = next(e for e in EXPERIENCE_LEVELS if e["slug"] == experience_level)

        department = _weighted_choice(
            self.rng,
            [d["slug"] for d in DEPARTMENTS],
            [d["weight"] for d in DEPARTMENTS],
        )
        department_meta = next(d for d in DEPARTMENTS if d["slug"] == department)

        category = self.rng.choice(JOB_CATEGORIES)

        employment_type = _weighted_choice(
            self.rng,
            [e["slug"] for e in EMPLOYMENT_TYPES],
            [e["weight"] for e in EMPLOYMENT_TYPES],
        )

        work_mode = _weighted_choice(
            self.rng,
            [w["slug"] for w in WORK_MODES],
            [w["weight"] for w in WORK_MODES],
        )

        education = _weighted_choice(
            self.rng,
            [e["slug"] for e in EDUCATION_LEVELS],
            [e["weight"] for e in EDUCATION_LEVELS],
        )

        status = _weighted_choice(
            self.rng,
            [s["slug"] for s in JOB_STATUSES],
            [s["weight"] for s in JOB_STATUSES],
        )

        salary_min, salary_max, currency = self._salary(company["country_code"], seniority, department, company.get("industry_slug", "software"))

        exp_min = self.rng.randint(seniority_meta["min_experience"], max(seniority_meta["min_experience"] + 1, seniority_meta["max_experience"] - 1))
        exp_max = exp_min + self.rng.randint(1, 4)
        exp_min = max(exp_min, experience_level_meta["min_years"])
        exp_max = max(exp_max, exp_min + 1)

        required_count = self.rng.randint(3, 7)
        preferred_count = self.rng.randint(2, 5)
        required_skills = self.rng.sample(skills_pool, k=min(required_count, len(skills_pool)))
        remaining = [s for s in skills_pool if s not in required_skills]
        preferred_skills = self.rng.sample(remaining, k=min(preferred_count, len(remaining)))

        focus = self.rng.choice(FOCUS_AREAS)
        description = self.rng.choice(JOB_DESCRIPTION_TEMPLATES).format(
            level=seniority_meta["name"], role_title=base_role,
            department=department_meta["name"], focus_area=focus,
        )
        responsibilities = [
            self.rng.choice(RESPONSIBILITY_TEMPLATES).format(tech=self.rng.choice(required_skills + ["various technologies"]))
            for _ in range(self.rng.randint(5, 8))
        ]
        requirements = [
            self.rng.choice(REQUIREMENT_TEMPLATES).format(
                years=self.rng.randint(exp_min, exp_max + 1),
                tech=self.rng.choice(required_skills + ["modern development"]),
            )
            for _ in range(self.rng.randint(5, 10))
        ]
        nice_to_have = [
            self.rng.choice(NICE_TO_HAVE_TEMPLATES).format(tech=self.rng.choice(preferred_skills + required_skills))
            for _ in range(self.rng.randint(3, 6))
        ]

        now = datetime.now(timezone.utc)
        created = now - timedelta(days=self.rng.randint(0, 180))
        deadline = created + timedelta(days=self.rng.randint(7, 90))
        if status in ("closed", "filled"):
            deadline = created + timedelta(days=self.rng.randint(7, 90))

        uid = str(uuid.uuid5(_NS, f"verifai.job.{company['_id']}.{uuid.uuid4().hex[:8]}"))

        return {
            "_id": uid,
            "title": title,
            "description": description,
            "responsibilities": responsibilities,
            "requirements": requirements,
            "nice_to_have": nice_to_have,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "currency": currency,
            "salary_period": "yearly",
            "experience_min": exp_min,
            "experience_max": exp_max,
            "education": education,
            "work_mode": work_mode,
            "remote": work_mode == "remote",
            "employment_type": employment_type,
            "experience_level": experience_level,
            "department": department,
            "category": category["slug"],
            "category_name": category["name"],
            "company_id": company["_id"],
            "company_slug": company["slug"],
            "company_name": company["name"],
            "recruiter_id": rec["_id"],
            "recruiter_name": rec.get("display_name", ""),
            "location_city": company["headquarters_city"],
            "location_state": company.get("headquarters_state"),
            "location_country": company["country"],
            "location_country_code": company["country_code"],
            "city_id": None,
            "openings": self.rng.choices([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], weights=[40, 25, 15, 8, 5, 3, 2, 1, 0.5, 0.5])[0],
            "application_deadline": deadline,
            "benefits": company.get("benefits", []),
            "required_skills": required_skills,
            "preferred_skills": preferred_skills,
            "tags": [category["slug"], department, work_mode, employment_type, seniority],
            "status": status,
            "applicants_count": self.rng.randint(0, 250) if status == "open" else self.rng.randint(0, 50),
            "views_count": self.rng.randint(50, 5000),
            "created_at": created,
            "updated_at": now - timedelta(days=self.rng.randint(0, 30)),
        }

    def _salary(self, country_code, seniority_slug, department_slug, industry_slug):
        country = next((c for c in COUNTRIES if c["code"] == country_code), COUNTRIES[1])
        currency = country["currency"]
        base = BASE_SALARY_USD.get(seniority_slug, BASE_SALARY_USD["mid"])
        industry_mult = INDUSTRY_SALARY_MULTIPLIER.get(industry_slug, 1.0)
        dept_mult = DEPARTMENT_SALARY_MULTIPLIER.get(department_slug, 1.0)
        country_mult = COUNTRY_PURCHASING_POWER.get(country_code, 1.0)
        usd_to_currency = CURRENCY_BASE_USD.get(currency, 1.0)

        base_min_usd = base["min"] * industry_mult * dept_mult * country_mult
        base_max_usd = base["max"] * industry_mult * dept_mult * country_mult

        jitter_min = self.rng.uniform(0.85, 1.15)
        jitter_max = self.rng.uniform(0.85, 1.15)
        base_min_local = (base_min_usd * jitter_min) / usd_to_currency
        base_max_local = (base_max_usd * jitter_max) / usd_to_currency

        if currency in ("JPY", "KRW", "INR"):
            base_min_local = round(base_min_local / 1000) * 1000
            base_max_local = round(base_max_local / 1000) * 1000
        else:
            base_min_local = round(base_min_local / 1000) * 1000
            base_max_local = round(base_max_local / 1000) * 1000

        if base_max_local <= base_min_local:
            base_max_local = base_min_local + int(base_min_local * 0.15)

        return int(base_min_local), int(base_max_local), currency


__all__ = ["JobsGenerator"]