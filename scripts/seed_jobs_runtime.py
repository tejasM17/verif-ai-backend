"""
Direct-Mongo job seeder that pairs with `seed_companies_runtime.py`.

For every MNC company already in `verifai.companies` (matched by
`company_name` against the MNC_COMPANIES list in `seed_companies_runtime.py`),
this script inserts 3-5 sample job documents into the new `verifai.jobs`
collection.

Each job document matches the `JobPublic` schema:
  - uid (deterministic so re-runs dedupe)
  - company_uid, recruiter_uid (== company_uid for the runtime seeder)
  - title, department, location, employment_type, work_mode, experience_level
  - description, required_skills (list[str])
  - salary_min, salary_max, currency
  - status ("open"), created_at, updated_at

Jobs cycle through a pool of titles and skill sets so each MNC looks
distinct. Salaries and experience levels vary by title. Re-runs are
idempotent — the uid namespace is `verifai.runtime.job.mnc.{slug}.{title_slug}.{i}`.

Run from the backend directory with the venv active:
    python scripts/seed_jobs_runtime.py
"""

from __future__ import annotations

import os
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone

# Allow `python scripts/seed_jobs_runtime.py` to find the `app` package.
_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from pymongo import MongoClient

# Use the same URI the app uses (MONGODB_URI env var, loaded by app.core.config).
from app.core.config import settings

# Re-use the canonical MNC company list from the previous seeder so we don't
# drift out of sync.
sys.path.insert(0, os.path.join(_BACKEND_ROOT, "scripts"))
from seed_companies_runtime import MNC_COMPANIES  # noqa: E402

DB_NAME = "verifai"
COMPANIES_COLL = "companies"
JOBS_COLL = "jobs"
_NS = uuid.NAMESPACE_DNS

# Per-company: pick between 3 and 5 jobs from the title pool (no repeats within a company).
JOBS_PER_COMPANY_MIN = 3
JOBS_PER_COMPANY_MAX = 5

# Title pool. Each tuple is (title, department, [experience_levels], salary_range_usd).
TITLE_POOL: list[tuple[str, str, list[str], tuple[int, int]]] = [
    ("Software Engineer", "Engineering", ["entry", "mid"], (110_000, 160_000)),
    ("Senior Software Engineer", "Engineering", ["mid", "senior"], (160_000, 220_000)),
    ("Machine Learning Engineer", "Data", ["mid", "senior"], (150_000, 210_000)),
    ("Product Manager", "Product", ["mid", "senior"], (140_000, 200_000)),
    ("Data Scientist", "Data", ["entry", "mid"], (120_000, 180_000)),
    ("DevOps Engineer", "Engineering", ["mid", "senior"], (130_000, 190_000)),
    ("Frontend Engineer", "Engineering", ["entry", "mid"], (110_000, 170_000)),
    ("Backend Engineer", "Engineering", ["entry", "mid", "senior"], (120_000, 190_000)),
    ("Engineering Manager", "Engineering", ["senior", "lead"], (200_000, 280_000)),
    ("UX Designer", "Design", ["entry", "mid"], (100_000, 160_000)),
]

# Skills pool — for each job title we'll pick a 4-6 subset, shuffled deterministically.
SKILL_POOL: dict[str, list[str]] = {
    "Software Engineer": [
        "Python", "Go", "Java", "REST APIs", "Git", "Docker", "Kubernetes",
        "AWS", "SQL", "Microservices", "Linux", "System Design",
    ],
    "Senior Software Engineer": [
        "System Design", "Distributed Systems", "Go", "Java", "Python",
        "Kubernetes", "AWS", "Mentorship", "Code Review", "Architecture",
    ],
    "Machine Learning Engineer": [
        "Python", "PyTorch", "TensorFlow", "MLOps", "Kubernetes",
        "Feature Stores", "A/B Testing", "CUDA", "Transformers", "SQL",
    ],
    "Product Manager": [
        "Roadmapping", "User Research", "Analytics", "SQL",
        "Stakeholder Management", "A/B Testing", "OKRs", "Strategy",
    ],
    "Data Scientist": [
        "Python", "R", "SQL", "Statistics", "Experimentation",
        "Pandas", "scikit-learn", "Tableau", "Causal Inference",
    ],
    "DevOps Engineer": [
        "Kubernetes", "Terraform", "AWS", "GCP", "CI/CD", "Prometheus",
        "Grafana", "Linux", "Ansible", "SRE",
    ],
    "Frontend Engineer": [
        "React", "TypeScript", "Next.js", "CSS", "Accessibility",
        "Testing", "GraphQL", "Webpack", "Vite",
    ],
    "Backend Engineer": [
        "Python", "Node.js", "PostgreSQL", "Redis", "gRPC",
        "REST APIs", "Kafka", "Docker", "AWS", "Distributed Systems",
    ],
    "Engineering Manager": [
        "Leadership", "Hiring", "Mentorship", "Roadmapping",
        "Cross-functional Collaboration", "OKRs", "Performance Reviews",
    ],
    "UX Designer": [
        "Figma", "User Research", "Prototyping", "Design Systems",
        "Accessibility", "Information Architecture", "Usability Testing",
    ],
}

WORK_MODES = ["remote", "hybrid", "on-site"]


def _slugify(value: str) -> str:
    return "".join(c.lower() if c.isalnum() else "" for c in value).strip() or "value"


def _description(title: str, company_name: str) -> str:
    return (
        f"Join {company_name} as a {title}. You'll work on high-impact projects "
        f"alongside a world-class team, shipping production-grade solutions to "
        f"millions of users. We value ownership, collaboration, and a learning mindset."
    )


def _build_job_doc(
    company: dict,
    company_uid: str,
    title: str,
    department: str,
    experience_levels: list[str],
    salary_range: tuple[int, int],
    rng: random.Random,
    idx: int,
    now: datetime,
) -> dict:
    location = company.get("location") or "Remote"
    work_mode = rng.choice(WORK_MODES)
    experience_level = rng.choice(experience_levels)
    skills_pool = SKILL_POOL.get(title, ["Communication", "Problem Solving"])
    skill_count = min(len(skills_pool), rng.randint(4, 6))
    required_skills = rng.sample(skills_pool, skill_count)

    salary_min, salary_max = salary_range
    # Add a small +/- jitter so listings aren't identical across MNCs.
    jitter = rng.randint(-10_000, 10_000)
    salary_min_adj = max(60_000, salary_min + jitter)
    salary_max_adj = max(salary_min_adj + 20_000, salary_max + jitter)

    company_slug = _slugify(company["company_name"])
    title_slug = _slugify(title)
    uid = str(uuid.uuid5(_NS, f"verifai.runtime.job.mnc.{company_slug}.{title_slug}.{idx}"))

    created = now - timedelta(days=rng.randint(0, 30))
    updated = created

    return {
        "uid": uid,
        "company_uid": company_uid,
        "recruiter_uid": company_uid,
        "title": title,
        "department": department,
        "location": location,
        "employment_type": "full-time",
        "work_mode": work_mode,
        "experience_level": experience_level,
        "description": _description(title, company["company_name"]),
        "required_skills": required_skills,
        "salary_min": float(salary_min_adj),
        "salary_max": float(salary_max_adj),
        "currency": "USD",
        "status": "open",
        "created_at": created,
        "updated_at": updated,
    }


def build_job_docs_for_company(
    company: dict,
    company_uid: str,
    now: datetime,
    seed: int,
) -> list[dict]:
    rng = random.Random(seed)
    # Pick JOBS_PER_COMPANY_MIN..JOBS_PER_COMPANY_MAX titles without repeats.
    count = rng.randint(JOBS_PER_COMPANY_MIN, JOBS_PER_COMPANY_MAX)
    count = min(count, len(TITLE_POOL))
    chosen = rng.sample(TITLE_POOL, count)
    docs: list[dict] = []
    for idx, (title, department, exp_levels, salary_range) in enumerate(chosen):
        docs.append(
            _build_job_doc(
                company=company,
                company_uid=company_uid,
                title=title,
                department=department,
                experience_levels=exp_levels,
                salary_range=salary_range,
                rng=rng,
                idx=idx,
                now=now,
            )
        )
    return docs


def main() -> None:
    if not settings.MONGODB_URI:
        raise SystemExit("MONGODB_URI is not set in .env")

    client = MongoClient(settings.MONGODB_URI)
    db = client[DB_NAME]
    companies_coll = db[COMPANIES_COLL]
    jobs_coll = db[JOBS_COLL]

    # Build a name -> company doc lookup so we can grab each MNC's uid.
    # When multiple companies share an MNC name (e.g. an old fictional entry),
    # prefer the one whose industry matches the MNC's expected industry in
    # MNC_COMPANIES, falling back to the most recently created entry.
    target_names = {entry[0] for entry in MNC_COMPANIES}
    expected_industry = {entry[0]: entry[3] for entry in MNC_COMPANIES}
    raw_docs = list(companies_coll.find({"company_name": {"$in": list(target_names)}}))
    if not raw_docs:
        raise SystemExit(
            "No MNC companies found in verifai.companies. "
            "Run scripts/seed_companies_runtime.py first."
        )

    by_name: dict[str, dict] = {}
    for doc in raw_docs:
        name = doc["company_name"]
        existing = by_name.get(name)
        expected = expected_industry.get(name)
        if existing is None:
            by_name[name] = doc
            continue
        # Prefer the doc whose industry matches the MNC's expected industry
        if expected and doc.get("industry") == expected and existing.get("industry") != expected:
            by_name[name] = doc
            continue
        if expected and existing.get("industry") == expected and doc.get("industry") != expected:
            continue
        # Tie-break: pick the most recently created doc
        if doc.get("created_at", doc.get("_id")) > existing.get("created_at", existing.get("_id")):
            by_name[name] = doc
    company_docs = list(by_name.values())

    now = datetime.now(timezone.utc)
    all_docs: list[dict] = []
    for company in company_docs:
        company_uid = company.get("uid")
        if not company_uid:
            continue
        # Use a per-company seed derived from the company name so the same
        # company always gets the same job selection across re-runs.
        seed = int(uuid.uuid5(_NS, f"verifai.runtime.jobs.seed.{company['company_name']}").int % (2**32))
        all_docs.extend(build_job_docs_for_company(company, company_uid, now, seed))

    existing_uids = {d["uid"] for d in jobs_coll.find({}, {"uid": 1, "_id": 0})}
    to_insert = [d for d in all_docs if d["uid"] not in existing_uids]

    if not to_insert:
        print(
            f"No new jobs to insert. Existing runtime rows: {len(existing_uids)}. "
            f"MNC companies processed: {len(company_docs)}."
        )
        return

    result = jobs_coll.insert_many(to_insert, ordered=False)
    avg = len(to_insert) / max(1, len(company_docs))
    print(
        f"Inserted {len(result.inserted_ids)} jobs into '{DB_NAME}.{JOBS_COLL}' "
        f"across {len(company_docs)} MNC companies "
        f"(avg {avg:.1f} jobs/company). "
        f"Skipped {len(all_docs) - len(to_insert)} already present."
    )


if __name__ == "__main__":
    main()
