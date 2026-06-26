# VerifAI Backend — AGENTS.md

Keep this file updated whenever routes, schema, or structure change. Minimal text, low context.

## Project rules
- strictly follow only the user task's context that what to implement or edit in backend project, and do not suggest your ideas.
- only focus on implementing the user task

## Recent Fixes / Known Bugs
- **`GET /me` returning `401 Unauthorized` for stale tokens (fixed 2026-06-25):** Firebase idTokens expire ~1h after issue. If the client still has an old `verifai_token` in localStorage, `verify_token()` returns `None` and `get_current_user` raises 401. The frontend's `AuthContext` already catches this and calls `removeToken()`. No backend fix needed — but if you add new protected endpoints, mirror this pattern: never raise on expired-token paths the client is allowed to retry.
- **`HTTPBearer401` swallows all HTTPException from `HTTPBearer`** (missing/malformed header → 401 instead of 403). Intentional — the contract is "no token OR bad token = 401". Do not "fix" by re-raising the original status; the frontend's axios interceptor relies on a consistent 401.
- **`verify_token` allows `clock_skew_seconds=10`** to absorb minor clock drift between client and Firebase. Do not set this to 0.
- **`reload_config()` mutates the `seed_config` singleton in-place** (does not rebind the global) because `from app.seed.config import seed_config` captures the original object reference. Fixed 2026-06-25 — do not regress by reintroducing `global seed_config; seed_config = _build_config()` style reassignment.
- **`_insert_one_batch` declares `skipped` before the schema-validation branch** (fixed 2026-06-25) so the bare-bulk path (`schema=None`) still returns `(inserted, skipped, 0)`. Do not move the `skipped = 0` back inside the `if self.schema is not None:` block.

## Run / Test / Lint
- do not run any tests until user mentions word "test" in their task.
```
cd verif-ai-backend
venv\Scripts\python.exe -m pip install -r requirements.txt
venv\Scripts\python.exe -m uvicorn main:app --reload    # API on :8000
venv\Scripts\python.exe -m pytest tests/ -v            # tests
venv\Scripts\python.exe -m ruff check .                # lint
venv\Scripts\python.exe -m ruff format .               # format
venv\Scripts\python.exe -m duckduckgo-mcp-server.exe   # MCP server (stdio)
```

## Seeder (offline tool — not part of the API)
- `app/seed/` package generates 5,000 companies, 50,000 recruiters, 250,000 jobs into Mongo + Firebase Auth.
- CLI: `python -m app.seed {run|resume|status|rollback|verify|firebase-sync}`. Full flag list via `--help`.
- Resumable: state in `seed_data/checkpoint.json`. Partial runs pick up where they left off (per-stage, with last-batch-id cursor).
- Idempotent: deterministic `uuid5(NAMESPACE_DNS, ...)` + unique indexes on `email`, `slug`, `firebase_uid`. Re-runs upsert; no duplicate-key errors abort the run.
- Deterministic: every generator uses `random.Random(seed_config.seed)` (default 42). Same inputs → same data.
- Skips the API hot path — does not import `app.api.*`. Uses `app.core.seed_database` (separate Mongo singleton, all 17 collections indexed).
- `seed_data/` is gitignored (`checkpoint.json`, `seed.log`, `seed_errors.log`, `seed_credentials.csv`).
- Tests in `tests/test_seed.py` use mongomock — no live DB required. Run alongside the rest with `pytest tests/`.

### Seeder CLI usage
```bash
cd verif-ai-backend
venv\Scripts\python.exe -m app.seed run                    # full run with defaults (5k/50k/250k)
venv\Scripts\python.exe -m app.seed run --workers 16 --batch-size 2000
venv\Scripts\python.exe -m app.seed run --skip-firebase    # Mongo only
venv\Scripts\python.exe -m app.seed run --stage jobs       # run only one stage
venv\Scripts\python.exe -m app.seed resume                  # continue after interrupt
venv\Scripts\python.exe -m app.seed status                  # per-stage progress + collection counts
venv\Scripts\python.exe -m app.seed verify                  # assert counts >= targets
venv\Scripts\python.exe -m app.seed rollback --yes          # drop all 17 seeded collections + reset checkpoint
venv\Scripts\python.exe -m app.seed firebase-sync --retry   # retry only recruiters where firebase_sync_status=pending

# wrappers:
./scripts/seed.sh
./scripts/rollback.sh
./scripts/verify.sh
```

### Seeder architecture
```
app/seed/
  __init__.py                  Re-exports SeedConfig / seed_config
  __main__.py                  python -m app.seed entrypoint → cli.main()
  cli.py                       argparse (run/resume/status/rollback/verify/firebase-sync)
  config.py                    SeedConfig singleton + apply_cli_overrides() + reload_config()
  logger.py                    Rotating file + stdout logger (one per seed log domain)
  checkpoint.py                Atomic JSON checkpoint store + StageProgress dataclass
  progress.py                  tqdm-style progress bars with ETA
  schemas.py                   17 Pydantic models (CountryDoc, JobDoc, RecruiterDoc, …)
  reference/                   Curated deterministic reference data
    countries.py               14 countries (ISO, locale, currency, timezone, langs)
    cities.py                  ~30 cities per country = 351 records with lat/lng/tz
    languages.py               24 languages with native names
    names.py                   First/last name pools per country
    industries.py              20 industries + weighted distributions (size, hiring, verification)
    roles.py                   30 job categories, 10 seniority levels, 12 departments, 5 employment types, 7 experience levels, 3 work modes, 6 education levels, 5 job statuses, recruiter designations + specialties
    benefits.py                32 benefits + culture templates + adjectives + industry phrases
    salaries.py                USD base × industry × country × dept multipliers → local currency
    skills.py                  ~700 curated skills in 12 categories (programming, frontend, backend, mobile, databases, cloud/devops, AI/ML, security, practices, soft skills, emerging, industry-specific, tools, data eng, web3)
    name_parts.py              ~200 name roots + 50 suffixes for company names
  generators/
    base.py                    BaseGenerator — chunked insert_many with retry, Pydantic validation, resume cursor
    countries.py               CountriesGenerator, StatesGenerator, CitiesGenerator
    skills.py                  SkillsGenerator (~1000 unique skills)
    companies.py               CompaniesGenerator (industry-themed tech stack, benefits, culture, ratings, social URLs)
    recruiters.py              RecruitersGenerator (writes 7 collections: recruiters + recruiter_profiles + recruiter_preferences + recruiter_verification + recruiter_notifications + recruiter_sessions + recruiter_activity)
    jobs.py                    JobsGenerator (50 jobs/company average, full schema: salary range, skills, requirements, benefits, status)
    related.py                 JobCategoriesGenerator, DepartmentsGenerator, EmploymentTypesGenerator, ExperienceLevelsGenerator
  firebase/
    bulk_auth.py               BulkAuthImporter — auth.import_users() in chunks of 500, exponential backoff, credentials CSV writer, retry-only-pending mode
  runners/
    orchestrator.py            Topological stage execution + checkpoint driver + status report

app/core/seed_database.py      Bulk-write Mongo wrapper: get_seed_client/db/collection, ensure_seed_indexes, drop_all_seed_collections, counts
```

### Seeded collections (MongoDB `verifai`)
| Collection | Target | Indexes |
|---|---|---|
| `countries` | 14 | `code` unique, `code3` unique |
| `states` | 103 | `(country_code, code)` unique |
| `cities` | 351 | `(country_code, state_code, name)` unique, `(country_code, name)`, (geospatial-ready) |
| `skills` | 1000 | `slug` unique, `category` |
| `job_categories` | 30 | `slug` unique |
| `departments` | 12 | `slug` unique |
| `employment_types` | 5 | `slug` unique |
| `experience_levels` | 7 | `slug` unique |
| `companies` | 5000 | `slug` unique, `industry`, `(country, industry)`, `verification_status`, `hiring_status`, `hq_country`, text(name+description+industry) |
| `recruiters` | 50000 | `email` unique, `firebase_uid` unique (sparse), `company_id`, `(company_id, active_status)`, `designation`, `country`, text(display_name+bio+designation) |
| `recruiter_profiles` | 50000 | `recruiter_id` unique, `company_id` |
| `recruiter_activity` | ~750k | `recruiter_id`, `(recruiter_id, created_at)`, `activity_type` |
| `recruiter_verification` | 50000 | `recruiter_id` unique, `status` |
| `recruiter_preferences` | 50000 | `recruiter_id` unique |
| `recruiter_notifications` | ~100k | `recruiter_id`, `(recruiter_id, read, created_at)` |
| `recruiter_sessions` | ~150k | `session_token` unique, `recruiter_id`, `(recruiter_id, created_at)` |
| `jobs` | 250000 | `(company_id, status)`, `(status, created_at)`, `recruiter_id`, `department`, `work_mode`, `employment_type`, `experience_level`, `country`, `required_skills` (multikey), `category`, text(title+description+department) |

### Firebase Auth sync
- Each recruiter has deterministic `firebase_uid = uuid5(NAMESPACE_DNS, "verifai.recruiter.<email>")` (matches Mongo `_id`).
- `python -m app.seed run` (no `--skip-firebase`) calls `firebase/bulk_auth.py` after recruiters land in Mongo: it reads every recruiter with `firebase_sync_status=pending`, then `auth.import_users([…], hash_algo=BCERT)` in chunks of 500 with exponential backoff (initial 1s, max 30s, 5 retries). Quota errors (`quota`, `rate limit`, `too many requests`) leave the recruiter as `pending` so `firebase-sync --retry` can resume.
- Credentials written to `seed_data/seed_credentials.csv` columns: `recruiter_id, email, password, display_name, company_id` — gitignored. Use any row to log in via the API and verify the seeded data round-trips.

### Known gaps / decisions
- **Quota**: free Firebase Spark plan allows ~30k new users/month. 50k recruiters will exceed this. The `--retry` flag is the recovery path — wait until next month, then `python -m app.seed firebase-sync --retry`.
- **Profile photos**: pravatar URLs (`https://i.pravatar.cc/300?u=<firebase_uid>`) — deterministic, no Mongo storage cost. Switch to real binaries later by adding a `--upload-photos` flag (would store base64 in `profile_photos`, ~2 GB cluster impact).
- **RTDB mirror**: off by default. Recruiter data lives only in Mongo. Add `--rtdb-mirror` to also write `/recruiters/{uid}` to RTDB (not needed for current `/companies/*` and `/applications/*` endpoints).
- **No transactions**: each collection seeded independently. Cross-collection consistency comes from the orchestrator's topological order — recruiters always reference a `company_id` that exists, jobs reference both.

## Required Env (.env)
- `FIREBASE_WEB_API_KEY` — Firebase Web API key (used for password sign-in REST call)
- `FIREBASE_CRED_PATH` — defaults to `firebase-key.json` (service-account JSON in repo root)
- `FIREBASE_DATABASE_URL` — RTDB URL, optional but needed for profile reads/writes
- `MONGODB_URI` — Mongo connection string, needed for resumes + photos + companies + applications + seeded data

## Routes (all under `/`)
| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/` | none | Health check |
| POST | `/signup` | none | Create user (email, password, optional role) |
| POST | `/login` | none | Email/password login, returns idToken |
| POST | `/google` | none | Verify Firebase Google idToken, returns app idToken |
| POST | `/github` | none | Verify Firebase GitHub idToken, returns app idToken |
| GET | `/me` | bearer | Current user profile |
| GET | `/profile/me` | bearer | Current user's full profile |
| PUT | `/profile/me` | bearer | Update own profile (role-aware field allow-list) |
| DELETE | `/profile/me` | bearer | Delete own profile |
| POST | `/profile/onboarding` | bearer | Set role + optional role-specific profile in one shot |
| PUT | `/profile/role` | bearer | Change role |
| GET | `/profile/student` | student | Student-scoped profile read |
| GET | `/profile/recruiter` | recruiter | Recruiter-scoped profile read |
| PUT | `/profile/photo` | bearer | Upload avatar (multipart, stored base64 in Mongo) |
| GET | `/profile/photo/{uid}` | none | Fetch avatar bytes |
| GET | `/profile/{uid}` | none | Fetch any profile by uid |
| POST | `/resume/upload` | student | Upload resume (PDF/DOC/DOCX/PNG/JPG, max 5MB) |
| GET | `/resume/me` | student | Own resume metadata |
| GET | `/resume/{uid}` | recruiter | Other student's resume metadata |
| GET | `/resume/file/{uid}` | none | Download resume bytes |
| DELETE | `/resume/me` | student | Delete own resume |
| POST | `/companies/me` | recruiter | Create/upsert my company profile (Mongo) |
| GET | `/companies/me` | recruiter | My company profile |
| PUT | `/companies/me` | recruiter | Patch my company profile (Mongo) |
| GET | `/companies/search` | none | Search companies `?q=&role=&location=&limit=&skip=` |
| GET | `/companies` | none | Paginated company feed (Instagram-style) |
| GET | `/companies/{uid}` | none | Public company profile |
| POST | `/applications/submit` | student | Submit application `{resume_uid, company_uid, why_appoint}` |
| GET | `/applications/me` | student | Student's "Applied Companies" tab |
| GET | `/applications/recruiter/me` | recruiter | Recruiter's "Applications" tab; `?status=submitted|reviewing|accepted|rejected` |
| GET | `/applications/{app_id}` | bearer | Get one application (student or recruiter owner only) |
| PATCH | `/applications/{app_id}/status` | recruiter | Update application status `{status, note}`; appends to `status_history` |

## Layered Architecture
```
HTTP  ─►  api/v1/*.py            (FastAPI routers, no business logic)
        ─►  api/dependencies.py  (get_current_user, require_student, require_recruiter)
        ─►  services/*.py        (business logic + 404/400 checks)
        ─►  repositories/*.py    (Firebase RTDB + Mongo, raw data access)
        ─►  domain/entities      (dataclass models)
        ─►  domain/enums         (UserRole = student | recruiter)
        ─►  schemas/             (Pydantic request/response models)
        ─►  core/                (config, db client, JWT verification, seed_database)

(offline)  seed/*               (not part of HTTP — runs as `python -m app.seed`)
        ─►  seed/reference       (curated deterministic lookup data)
        ─►  seed/generators      (chunked insert_many with retry)
        ─►  seed/firebase        (bulk auth import)
        ─►  seed/runners         (orchestrator, topologically ordered)
```

## Auth Flow (firebase only)
1. Client posts email/password OR social idToken to a `/login` / `/google` / `/github` endpoint
2. Backend returns Firebase `idToken`
3. Client stores idToken in localStorage (`verifai_token`) and sends it as `Authorization: Bearer <token>` on every subsequent call
4. `get_current_user` dependency verifies idToken, lazily creates the user profile in RTDB on first authenticated request, injects `{uid, email, displayName, photoUrl, role}` into the route handler
5. `require_student` / `require_recruiter` 403 if `current_user.role` doesn't match

## Profile Schema (Firebase RTDB `/users/{uid}`)
- `uid`, `email` — required
- `display_name`, `photo_url`, `resume_url` — optional
- `role` — `"student"` | `"recruiter"` (set by `/profile/onboarding` or `/profile/role`)
- `skills` — list of strings (student only)
- `company_name`, `company_email` — optional (recruiter only)
- `role_title`, `location` — optional (recruiter only) — the role they're hiring for + company location

Student-allowed update fields: `display_name`, `photo_url`, `resume_url`, `skills`
Recruiter-allowed update fields: `display_name`, `photo_url`, `company_name`, `company_email`, `role_title`, `location`

## Recruiter Schema (Pydantic, `app/schemas/recruiter.py`)
```python
class RecruiterProfile(BaseModel):
    uid: str
    email: EmailStr
    display_name: Optional[str] = None
    photo_url: Optional[str] = None
    role: UserRole = UserRole.recruiter

    company_name: Optional[str] = None
    company_email: Optional[str] = None
    role_title: Optional[str] = None      # the role they're hiring for
    location: Optional[str] = None        # company location
```

## Resumes / Photos (MongoDB)
- DB: `verifai`, collections: `resumes`, `profile_photos`
- One document per uid (`upsert` on save, `delete_one` on remove)
- Stored fields: `uid`, `filename`, `mime`, `data` (raw bytes)
- Allowed MIME types: PDF, DOC, DOCX, PNG, JPEG
- 5 MB size limit enforced client-side; backend does not enforce size

## Companies (MongoDB — collection `companies`)
- One document per recruiter (keyed by `uid`, unique index)
- Stored fields: `uid`, `company_name`, `role`, `location`, `description`, `website`, `industry`, `company_size`, `logo_url`, `follower_count`, `open_roles_count`, `created_at`, `updated_at`
- Text index on `(company_name, role, location)` for `/companies/search`
- Public read; only the owning recruiter can write via `/companies/me`
- Service syncs `company_name`, `role_title`, `location` back to Firebase RTDB profile on every upsert (keeps the two stores consistent)

## Applications (MongoDB — collection `applications`)
- One document per `(student_uid, company_uid)` (compound unique index — prevents double-application)
- Stored fields: `student_uid`, `recruiter_uid`, `company_uid`, `resume_uid`, `why_appoint`, `status`, `status_history[]`, `created_at`, `updated_at`
- `status` ∈ `{submitted, reviewing, accepted, rejected}`
- `status_history` is append-only — every status change records `{status, changed_at, note}`
- Indexes: `(recruiter_uid, status)` for recruiter dashboard, `(student_uid, created_at)` for student "Applied Companies"
- Enriched list responses (`/applications/me`, `/applications/recruiter/me`) join the student profile (RTDB) or company profile (Mongo) so the frontend gets one round-trip

## Roles
- `UserRole.student` → can upload resume, edit skills, submit applications, fetch own applications
- `UserRole.recruiter` → can fetch any student's resume, manage own company profile, list/update applications on own dashboard
- Default for first-time social login: `student`

## Code Style Rules
- No inline comments
- Files minimal, single responsibility
- Routers do not raise domain errors directly — services do
- Pydantic schemas at the boundary, dataclass entities in the domain layer
- Always keep `requirements.txt` updated when adding pip packages
- Seed package follows the same no-in

line-comments / single-responsibility rules
