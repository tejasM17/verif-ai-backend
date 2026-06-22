# AGENTS.md

always keep this file updated. minimal text.

## Project
FastAPI + Firebase Authentication + role-based auth for VerifAI.

## Stack
- Python 3.x, FastAPI
- Firebase Admin SDK (email/password, Google, GitHub auth)
- Firebase Realtime Database (user profiles + roles)
- Bearer token auth on protected routes
- Role guards: `require_student`, `require_recruiter`

## Code Style
- No inline comments
- Keep files minimal
- Clean layered architecture

## Commands
- Run: `uvicorn main:app --reload`
- Lint: `ruff check .`
- Format: `ruff format .`
- Test: `pytest tests/ -v`
- Test watch: `pytest tests/ -v --looponfail`

## Structure
```
main.py                      # Entry point — creates FastAPI app, includes routers
app/
  core/
    config.py                # Settings, env, Firebase init (+ databaseURL)
    security.py              # HTTPBearer dependency, token verification
  domain/
    enums/role.py            # UserRole enum (student, recruiter)
    entities/user.py         # UserEntity dataclass
  schemas/
    auth.py                  # Pydantic request/response models
    user.py                  # StudentProfile, RecruiterProfile, RoleUpdate
  api/
    dependencies.py          # get_current_user, require_student, require_recruiter
    v1/
      auth.py                # Auth routes (/signup, /login, /google, /github, /me)
      profile.py             # Profile routes (/profile/me, /profile/onboarding, /profile/student, /profile/recruiter)
  services/
    auth_service.py          # Auth business logic (login, signup, token verify)
    user_service.py          # Profile business logic (get/create, set role, update)
  repositories/
    firebase_repository.py   # Firebase Admin + REST data access
    user_repository.py       # Firebase RTDB CRUD for user profiles
```

## Auth Flow
1. User authenticates via Firebase (email/password, Google, GitHub)
2. Backend verifies Firebase ID token on every protected request
3. Backend checks/creates user profile in Firebase RTDB
4. Profile stores assigned role (student/recruiter)
5. Role guards check role from profile data
