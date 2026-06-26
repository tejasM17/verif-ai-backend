import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Iterator

from app.core.seed_database import get_seed_db
from app.seed.checkpoint import StageProgress
from app.seed.config import seed_config
from app.seed.generators.base import BaseGenerator
from app.seed.reference.countries import COUNTRIES
from app.seed.reference.industries import INDUSTRY_BY_SLUG
from app.seed.reference.languages import LANGUAGES
from app.seed.reference.names import FIRST_NAMES_BY_COUNTRY, LAST_NAMES_BY_COUNTRY
from app.seed.reference.roles import RECRUITER_DESIGNATIONS, RECRUITER_SPECIALTIES
from app.seed.reference.skills import SKILLS
from app.seed.schemas import (
    RecruiterActivityDoc, RecruiterDoc, RecruiterNotificationDoc,
    RecruiterPreferencesDoc, RecruiterProfileDoc, RecruiterSessionDoc,
    RecruiterVerificationDoc,
)
from app.seed.logger import get_logger

logger = get_logger("seed.recruiters")

_NS = uuid.NAMESPACE_DNS


def _slugify(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip().lower()).strip("-")
    return s[:80] or "user"


def _weighted_choice(rng, items, weights):
    total = sum(weights)
    pick = rng.uniform(0, total)
    cur = 0.0
    for item, w in zip(items, weights):
        cur += w
        if pick <= cur:
            return item
    return items[-1]


ACTIVITY_TYPES = [
    ("login", "Logged in", 0.30),
    ("profile_view", "Viewed candidate profile", 0.20),
    ("job_posted", "Posted a new job", 0.05),
    ("job_updated", "Updated a job posting", 0.05),
    ("candidate_shortlisted", "Shortlisted a candidate", 0.10),
    ("candidate_rejected", "Rejected a candidate", 0.10),
    ("message_sent", "Sent a message", 0.10),
    ("interview_scheduled", "Scheduled an interview", 0.05),
    ("offer_extended", "Extended an offer", 0.02),
    ("settings_changed", "Updated account settings", 0.03),
]

NOTIFICATION_TYPES = [
    ("application_received", "New application received", "A candidate applied to one of your job postings."),
    ("candidate_message", "New candidate message", "You have a new message from a candidate."),
    ("interview_reminder", "Interview reminder", "You have an interview scheduled in 1 hour."),
    ("job_expiring", "Job posting expiring soon", "One of your job postings will expire in 3 days."),
    ("profile_view", "Profile view", "A candidate viewed your company profile."),
    ("system", "System update", "We've made improvements to your dashboard."),
]

DEVICES = ["MacBook Pro", "Windows Desktop", "iPhone 15", "Samsung Galaxy S23", "MacBook Air", "iPad Pro", "Linux Workstation"]


class RecruitersGenerator(BaseGenerator):
    """Generates recruiters + 6 related collections.

    Yields tuples of (primary_collection, doc) so the parent orchestrator
    can route each doc to the right collection. The `insert_batches` pattern
    only supports single-collection batches, so this generator instead exposes
    a `run()` that iterates all recruiters and dispatches each tuple through
    bulk writes to the appropriate collection.
    """

    collection_name = "recruiters"
    schema = RecruiterDoc

    def run(self) -> StageProgress:
        cfg = seed_config
        target = cfg.target_recruiters

        companies = self._load_companies()
        if not companies:
            logger.error("no_companies_found run companies stage first")
            self.checkpoint.mark_error(self.stage, "no companies in db")
            return self.checkpoint.get_stage(self.stage)

        company_targets = self._allocate_recruiters_per_company(companies, target)

        existing = self.checkpoint.get_stage(self.stage)
        if existing and existing.status == "completed" and existing.inserted >= target:
            logger.info("skip_completed stage=%s inserted=%d", self.stage, existing.inserted)
            return existing

        batches = max(1, (target + cfg.batch_size - 1) // cfg.batch_size)
        self.checkpoint.mark_running(self.stage, target, batches)

        stats = self._dispatch_recruiters(companies, company_targets)

        self.checkpoint.mark_completed(self.stage)
        logger.info(
            "stage_done stage=%s recruiters=%d activity=%d notif=%d session=%d profile=%d pref=%d verif=%d",
            self.stage, stats["recruiters"], stats["activity"], stats["notifications"],
            stats["sessions"], stats["profiles"], stats["preferences"], stats["verifications"],
        )
        return self.checkpoint.get_stage(self.stage)

    def _load_companies(self) -> list[dict]:
        coll = get_seed_db()["companies"]
        return list(coll.find({}, {
            "_id": 1, "slug": 1, "name": 1, "industry_slug": 1,
            "tech_stack": 1, "benefits": 1, "country_code": 1, "country": 1,
            "headquarters_city": 1, "headquarters_state": 1,
        }))

    def _allocate_recruiters_per_company(self, companies: list[dict], target: int) -> dict[str, int]:
        n = len(companies)
        if n == 0:
            return {}
        avg = target / n
        result: dict[str, int] = {}
        total = 0
        for i, c in enumerate(companies):
            r = self.rng.random()
            if r < 0.60:
                count = self.rng.randint(5, min(30, max(5, int(avg * 0.6))))
            elif r < 0.90:
                count = self.rng.randint(30, min(80, max(30, int(avg * 1.3))))
            else:
                count = self.rng.randint(80, min(200, max(80, int(avg * 2.5))))
            result[c["_id"]] = count
            total += count
        if total > target:
            scale = target / total
            result = {k: max(1, int(v * scale)) for k, v in result.items()}
        elif total < target * 0.95:
            deficit = target - total
            biggest = sorted(result.items(), key=lambda kv: -kv[1])
            for i in range(deficit):
                cid = biggest[i % len(biggest)][0]
                result[cid] += 1
        return result

    def _dispatch_recruiters(self, companies: list[dict], targets: dict[str, int]) -> dict[str, int]:
        db = get_seed_db()
        recruiters_coll = db["recruiters"]
        profiles_coll = db["recruiter_profiles"]
        prefs_coll = db["recruiter_preferences"]
        verif_coll = db["recruiter_verification"]
        notif_coll = db["recruiter_notifications"]
        sessions_coll = db["recruiter_sessions"]
        activity_coll = db["recruiter_activity"]

        recruiters_batch: list[dict] = []
        profiles_batch: list[dict] = []
        prefs_batch: list[dict] = []
        verifs_batch: list[dict] = []
        notifs_batch: list[dict] = []
        sessions_batch: list[dict] = []
        activity_batch: list[dict] = []

        stats = {
            "recruiters": 0, "activity": 0, "notifications": 0, "sessions": 0,
            "profiles": 0, "preferences": 0, "verifications": 0,
        }
        buf = cfg = seed_config.batch_size

        seen_emails: set[str] = self._existing_emails(recruiters_coll)

        total = sum(targets.values())
        logger.info("recruiter_generation_start companies=%d target=%d", len(companies), total)

        for company in companies:
            count = targets.get(company["_id"], 0)
            if count == 0:
                continue

            company_skills = company.get("tech_stack", [])[:15]
            industry_slug = company.get("industry_slug", "software")
            industry = INDUSTRY_BY_SLUG.get(industry_slug, INDUSTRY_BY_SLUG["software"])
            company_recruiters: list[dict] = []

            for _ in range(count):
                email = self._unique_email(company["slug"], seen_emails)
                seen_emails.add(email)
                rec = self._build_recruiter(company, email, company_skills, industry_slug)
                company_recruiters.append(rec)
                recruiters_batch.append(rec)
                profiles_batch.append(self._build_profile(rec))
                prefs_batch.append(self._build_preferences(rec))
                verifs_batch.append(self._build_verification(rec))
                notifs_batch.extend(self._build_notifications(rec))
                sessions_batch.extend(self._build_sessions(rec))
                activity_batch.extend(self._build_activity(rec))

                if len(recruiters_batch) >= buf:
                    self._flush(recruiters_batch, recruiters_coll, stats, "recruiters")
                    self._flush(profiles_batch, profiles_coll, stats, "profiles")
                    self._flush(prefs_batch, prefs_coll, stats, "preferences")
                    self._flush(verifs_batch, verif_coll, stats, "verifications")
                    self._flush(notifs_batch, notif_coll, stats, "notifications")
                    self._flush(sessions_batch, sessions_coll, stats, "sessions")
                    self._flush(activity_batch, activity_coll, stats, "activity")
                    self.checkpoint.mark_batch(self.stage, len(company_recruiters), 0, rec["_id"])
                    company_recruiters.clear()

            if recruiters_batch:
                self._flush(recruiters_batch, recruiters_coll, stats, "recruiters")
                self._flush(profiles_batch, profiles_coll, stats, "profiles")
                self._flush(prefs_batch, prefs_coll, stats, "preferences")
                self._flush(verifs_batch, verif_coll, stats, "verifications")
                self._flush(notifs_batch, notif_coll, stats, "notifications")
                self._flush(sessions_batch, sessions_coll, stats, "sessions")
                self._flush(activity_batch, activity_coll, stats, "activity")

        return stats

    def _existing_emails(self, coll) -> set[str]:
        return {d["email"] for d in coll.find({}, {"email": 1})}

    def _unique_email(self, company_slug: str, seen: set[str]) -> str:
        for attempt in range(50):
            first = self.rng.choice(FIRST_NAMES_BY_COUNTRY.get("US", ["user"])).lower()
            last = self.rng.choice(LAST_NAMES_BY_COUNTRY.get("US", ["user"])).lower()
            email = f"{first}.{last}@{company_slug}.verifai.test"
            if email not in seen:
                return email
            email = f"{first}.{last}.{attempt}@{company_slug}.verifai.test"
            if email not in seen:
                return email
        return f"recruiter.{uuid.uuid4().hex[:8]}@{company_slug}.verifai.test"

    def _flush(self, batch: list[dict], coll, stats: dict, key: str) -> None:
        if not batch:
            return
        if self.schema is not None and key == "recruiters":
            valid: list[dict] = []
            for doc in batch:
                try:
                    valid.append(self.schema.model_validate(doc).to_mongo())
                except Exception as exc:
                    self.error_logger().error("schema_validation_failed id=%s err=%s", doc.get("_id"), exc)
            batch = valid
        try:
            coll.insert_many(batch, ordered=False)
            stats[key] += len(batch)
        except Exception as exc:
            from pymongo.errors import BulkWriteError
            if isinstance(exc, BulkWriteError):
                details = exc.details or {}
                errs = details.get("writeErrors", [])
                dup = sum(1 for e in errs if e.get("code") == 11000)
                stats[key] += max(0, len(batch) - len(errs))
                if len(errs) > dup:
                    self.error_logger().error(
                        "bulk_write_errors collection=%s dup=%d non_dup=%d",
                        coll.name, dup, len(errs) - dup,
                    )
            else:
                self.error_logger().error("mongo_error collection=%s err=%s", coll.name, exc)

    def _build_recruiter(self, company: dict, email: str, tech_stack: list[str], industry_slug: str) -> dict:
        country_code = company["country_code"]
        country_data = next((c for c in COUNTRIES if c["code"] == country_code), COUNTRIES[1])
        first_pool = FIRST_NAMES_BY_COUNTRY.get(country_code, FIRST_NAMES_BY_COUNTRY["US"])
        last_pool = LAST_NAMES_BY_COUNTRY.get(country_code, LAST_NAMES_BY_COUNTRY["US"])
        first = self.rng.choice(first_pool)
        last = self.rng.choice(last_pool)
        display_name = f"{first} {last}"
        uid = str(uuid.uuid5(_NS, f"verifai.recruiter.{email}"))

        years_exp = self.rng.randint(1, 20)
        designation = self.rng.choice(RECRUITER_DESIGNATIONS)
        languages = self.rng.sample(country_data["languages"], k=min(len(country_data["languages"]), self.rng.randint(1, 4)))
        if "en" not in languages:
            languages.append("en")
        lang_codes = languages[:5]

        specialties = self.rng.sample(RECRUITER_SPECIALTIES, k=min(len(RECRUITER_SPECIALTIES), self.rng.randint(3, 6)))
        preferred_techs = self.rng.sample(tech_stack, k=min(len(tech_stack), self.rng.randint(4, 10))) if tech_stack else []
        if len(preferred_techs) < 4:
            fallback_pool: list[str] = []
            for sub in SKILLS.get(industry_slug.title(), {}).values() if industry_slug.title() in SKILLS else []:
                fallback_pool.extend(sub)
            if not fallback_pool:
                for sub in SKILLS.get("Programming", {}).values():
                    fallback_pool.extend(sub)
            preferred_techs.extend(self.rng.sample(fallback_pool, k=min(len(fallback_pool), 8 - len(preferred_techs))))

        verification_badge = self.rng.random() < 0.40
        active = self.rng.random() < 0.92
        online = active and self.rng.random() < 0.30
        now = datetime.now(timezone.utc)
        last_login = now - timedelta(days=self.rng.randint(0, 30), hours=self.rng.randint(0, 23))
        created = now - timedelta(days=self.rng.randint(60, 1500))

        city_name = company["headquarters_city"]
        state = company.get("headquarters_state")
        phone = f"{country_data['dial_code']}{self.rng.randint(7000000000, 9999999999)}"
        linkedin_slug = _slugify(f"{first}-{last}-{company['slug']}")

        return {
            "_id": uid,
            "email": email,
            "firebase_uid": None,
            "firebase_sync_status": "pending",
            "display_name": display_name,
            "photo_url": f"https://i.pravatar.cc/300?u={uid}",
            "company_id": company["_id"],
            "company_slug": company["slug"],
            "company_name": company["name"],
            "designation": designation,
            "bio": self._bio(designation, industry_slug, preferred_techs, country_code, years_exp),
            "years_experience": years_exp,
            "specialties": specialties,
            "preferred_technologies": preferred_techs,
            "languages": lang_codes,
            "language_names": [LANGUAGES[l]["name"] for l in lang_codes if l in LANGUAGES],
            "timezone": country_data["default_timezone"],
            "country": country_data["name"],
            "country_code": country_code,
            "state": state,
            "state_code": None,
            "city": city_name,
            "city_id": None,
            "phone": phone,
            "linkedin_url": f"https://linkedin.com/in/{linkedin_slug}",
            "verification_badge": verification_badge,
            "active_status": active,
            "online_status": online,
            "last_login": last_login,
            "created_at": created,
            "updated_at": now - timedelta(days=self.rng.randint(0, 60)),
        }

    def _bio(self, designation: str, industry_slug: str, techs: list[str], country_code: str, years: int) -> str:
        industry = INDUSTRY_BY_SLUG.get(industry_slug, INDUSTRY_BY_SLUG["software"])
        tech_list = ", ".join(techs[:5]) if techs else "various technologies"
        return (
            f"{designation} with {years}+ years of experience hiring top talent across {industry['name'].lower()}. "
            f"Based in {country_code}, I partner with hiring managers to build high-performing teams. "
            f"Specialized in roles leveraging {tech_list}. "
            f"Passionate about creating exceptional candidate experiences and helping people find roles they love."
        )

    def _build_profile(self, rec: dict) -> dict:
        return {
            "_id": str(uuid.uuid5(_NS, f"verifai.recruiter_profile.{rec['_id']}")),
            "recruiter_id": rec["_id"],
            "company_id": rec["company_id"],
            "headline": f"{rec['designation']} at {rec['company_name']}",
            "about": rec["bio"],
            "skills": rec["preferred_technologies"],
            "experience": [
                {
                    "title": rec["designation"],
                    "company": rec["company_name"],
                    "start_date": (rec["created_at"]).isoformat(),
                    "current": True,
                    "description": rec["bio"],
                },
                {
                    "title": self.rng.choice(RECRUITER_DESIGNATIONS),
                    "company": f"Previous Company {self.rng.randint(1, 999)}",
                    "start_date": (rec["created_at"] - timedelta(days=self.rng.randint(365, 3650))).isoformat(),
                    "end_date": rec["created_at"].isoformat(),
                    "current": False,
                    "description": "Recruited across multiple functions and geographies.",
                },
            ],
            "education": [
                {
                    "degree": self.rng.choice(["Bachelor of Business Administration", "Bachelor of Arts", "Master of Human Resources", "MBA"]),
                    "institution": f"{rec['country']} State University",
                    "year": self.rng.randint(2005, 2020),
                }
            ],
            "certifications": [],
            "social_links": {"linkedin": rec["linkedin_url"]},
            "languages": [{"code": l, "name": LANGUAGES.get(l, {}).get("name", l), "proficiency": "native" if l == rec.get("country_code", "").lower() else "fluent"} for l in rec["languages"]],
            "preferences": {"job_alerts": True, "email_notifications": True},
        }

    def _build_preferences(self, rec: dict) -> dict:
        return {
            "_id": str(uuid.uuid5(_NS, f"verifai.recruiter_preferences.{rec['_id']}")),
            "recruiter_id": rec["_id"],
            "job_alerts": True,
            "email_notifications": True,
            "push_notifications": self.rng.random() < 0.7,
            "sms_notifications": False,
            "weekly_digest": True,
            "preferred_job_types": self.rng.sample(["full_time", "contract", "internship"], k=self.rng.randint(1, 3)),
            "preferred_locations": [rec["city"]],
            "preferred_remote": self.rng.sample(["remote", "hybrid", "onsite"], k=self.rng.randint(1, 3)),
            "min_salary": self.rng.choice([50000, 80000, 100000, 150000]),
            "max_salary": self.rng.choice([150000, 250000, 400000]),
            "preferred_industries": [rec.get("country_code", "US")],
            "updated_at": rec["updated_at"],
        }

    def _build_verification(self, rec: dict) -> dict:
        email_v = self.rng.random() < 0.95
        phone_v = self.rng.random() < 0.80
        identity_v = self.rng.random() < 0.50
        company_v = self.rng.random() < 0.70
        bg_v = self.rng.random() < 0.30
        score = (email_v + phone_v + identity_v + company_v + bg_v) / 5.0
        status = "verified" if score >= 0.7 else "pending" if score >= 0.4 else "unverified"
        return {
            "_id": str(uuid.uuid5(_NS, f"verifai.recruiter_verification.{rec['_id']}")),
            "recruiter_id": rec["_id"],
            "status": status,
            "email_verified": email_v,
            "phone_verified": phone_v,
            "identity_verified": identity_v,
            "company_verified": company_v,
            "background_check": bg_v,
            "verified_at": rec["last_login"] if status == "verified" else None,
            "verification_score": round(score, 2),
            "documents": [],
        }

    def _build_notifications(self, rec: dict) -> list[dict]:
        out: list[dict] = []
        for _ in range(self.rng.randint(1, 3)):
            n_type, title, msg = self.rng.choice(NOTIFICATION_TYPES)
            created = rec["last_login"] - timedelta(days=self.rng.randint(0, 30))
            read = self.rng.random() < 0.4
            out.append({
                "_id": str(uuid.uuid5(_NS, f"verifai.notification.{rec['_id']}.{uuid.uuid4().hex[:8]}")),
                "recruiter_id": rec["_id"],
                "type": n_type,
                "title": title,
                "message": msg,
                "read": read,
                "action_url": None,
                "created_at": created,
                "read_at": created + timedelta(hours=self.rng.randint(1, 48)) if read else None,
            })
        return out

    def _build_sessions(self, rec: dict) -> list[dict]:
        out: list[dict] = []
        for i in range(self.rng.randint(1, 4)):
            created = rec["last_login"] - timedelta(days=self.rng.randint(0, 30))
            out.append({
                "_id": str(uuid.uuid5(_NS, f"verifai.session.{rec['_id']}.{uuid.uuid4().hex[:8]}")),
                "session_token": uuid.uuid4().hex + uuid.uuid4().hex[:16],
                "recruiter_id": rec["_id"],
                "ip_address": f"{self.rng.randint(1, 255)}.{self.rng.randint(0, 255)}.{self.rng.randint(0, 255)}.{self.rng.randint(1, 254)}",
                "user_agent": self.rng.choice([
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)",
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                ]),
                "device": self.rng.choice(DEVICES),
                "location": f"{rec['city']}, {rec['country']}",
                "active": i == 0 and self.rng.random() < 0.6,
                "created_at": created,
                "last_active": created + timedelta(hours=self.rng.randint(0, 12)),
                "expires_at": created + timedelta(days=30),
            })
        return out

    def _build_activity(self, rec: dict) -> list[dict]:
        out: list[dict] = []
        types = [a[0] for a in ACTIVITY_TYPES]
        weights = [a[2] for a in ACTIVITY_TYPES]
        for _ in range(self.rng.randint(5, 20)):
            atype = _weighted_choice(self.rng, types, weights)
            desc = next((a[1] for a in ACTIVITY_TYPES if a[0] == atype), "Activity")
            created = rec["last_login"] - timedelta(days=self.rng.randint(0, 60), hours=self.rng.randint(0, 23))
            out.append({
                "_id": str(uuid.uuid5(_NS, f"verifai.activity.{rec['_id']}.{uuid.uuid4().hex[:8]}")),
                "recruiter_id": rec["_id"],
                "activity_type": atype,
                "description": desc,
                "metadata": {"source": "seed"},
                "ip_address": f"{self.rng.randint(1, 255)}.{self.rng.randint(0, 255)}.{self.rng.randint(0, 255)}.{self.rng.randint(1, 254)}",
                "created_at": created,
            })
        return out


__all__ = ["RecruitersGenerator"]