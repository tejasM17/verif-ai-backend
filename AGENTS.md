# VerifAI Backend — AGENTS.md

Keep this file updated whenever routes, schema, or structure change. Minimal text, low context.

## Project rules
- strictly follow only the user taks's context that what to implement or edit in backend project, and dod not suggest your ideas.
- only focus on implementing the user task


## Run / Test / Lint
- do not run any tests untill user mention word "test" in their task.
```
cd verif-ai-backend
venv\Scripts\python.exe -m pip install -r requirements.txt
venv\Scripts\python.exe -m uvicorn main:app --reload    # API on :8000
venv\Scripts\python.exe -m pytest tests/ -v            # tests
venv\Scripts\python.exe -m ruff check .                # lint
venv\Scripts\python.exe -m ruff format .               # format
venv\Scripts\python.exe -m duckduckgo-mcp-server.exe   # MCP server (stdio)
```

## Required Env (.env)
- `FIREBASE_WEB_API_KEY` — Firebase Web API key (used for password sign-in REST call)
- `FIREBASE_CRED_PATH` — defaults to `firebase-key.json` (service-account JSON in repo root)
- `FIREBASE_DATABASE_URL` — RTDB URL, optional but needed for profile reads/writes
- `MONGODB_URI` — Mongo connection string, needed for resumes + photos

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

## Layered Architecture
```
HTTP  ─►  api/v1/*.py            (FastAPI routers, no business logic)
        ─►  api/dependencies.py  (get_current_user, require_student, require_recruiter)
        ─►  services/*.py        (business logic + 404/400 checks)
        ─►  repositories/*.py    (Firebase RTDB + Mongo, raw data access)
        ─►  domain/entities      (dataclass models)
        ─►  domain/enums         (UserRole = student | recruiter)
        ─►  schemas/             (Pydantic request/response models)
        ─►  core/                (config, db client, JWT verification)
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

Student-allowed update fields: `display_name`, `photo_url`, `resume_url`, `skills`
Recruiter-allowed update fields: `display_name`, `photo_url`, `company_name`, `company_email`

## Resumes / Photos (MongoDB)
- DB: `verifai`, collections: `resumes`, `profile_photos`
- One document per uid (`upsert` on save, `delete_one` on remove)
- Stored fields: `uid`, `filename`, `mime`, `data` (raw bytes)
- Allowed MIME types: PDF, DOC, DOCX, PNG, JPEG
- 5 MB size limit enforced client-side; backend does not enforce size

## Roles
- `UserRole.student` → can upload resume, edit skills, fetch own resume
- `UserRole.recruiter` → can fetch any student's resume via `/resume/{uid}`
- Default for first-time social login: `student`

## Code Style Rules
- No inline comments
- Files minimal, single responsibility
- Routers do not raise domain errors directly — services do
- Pydantic schemas at the boundary, dataclass entities in the domain layer
- Always keep `requirements.txt` updated when adding pip packages
