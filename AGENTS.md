# VerifAI Backend — Agent Guide

## Quick start

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API: http://localhost:8000
- Docs: http://localhost:8000/docs

## Architecture

| Layer | Technology | Key files |
|-------|-----------|-----------|
| Auth | Firebase Admin SDK (`firebase-admin==6.6.0`) | `app/auth/firebase.py` |
| Database | MongoDB (`pymongo`) + Firestore | `app/database/mongodb.py`, `app/database/session.py` |
| JWT | `python-jose[cryptography]` HS256 | `app/core/security.py` |
| API | FastAPI | `app/api/auth.py`, `app/main.py` |

- Firebase project ID: `verifai111` (`app/config/settings.py:12`)
- Users collection in MongoDB: `users`
- Profile collections: `students`, `recruiters` (Firestore)
- Lookup key is `firebase_uid` (not email), consistent across register and login
- Service account resolved from `firebase-service-account.json` (file) or `.env` vars (fallback)

## Session strategy: HTTP-only cookies + backend JWT

The backend uses **one consistent session strategy**: HTTP-only cookies for transport, backend-signed JWTs for the session owner.

- **Access token** (short-lived, 15min default) — stored in `access_token` cookie (path=/)
- **Refresh token** (long-lived, 7d default) — stored in `refresh_token` cookie (path=/)
- Both cookies are `HttpOnly` — JavaScript cannot read them
- Tokens contain `jti` (unique ID) for rotation detection
- Cookie `SameSite`/`Secure` configured via `COOKIE_SAMESITE` / `COOKIE_SECURE` settings

### How page refresh works
1. Frontend calls `GET /auth/me` on app init
2. Backend reads `access_token` cookie → validates JWT → returns user with role
3. If access token expired but refresh token valid → `/auth/me` auto-refreshes, sets new cookies
4. If both expired → `TOKEN_EXPIRED` → user sees login
5. **No frontend React state is the single source of truth** — the backend session survives reload

### Protected endpoints support both auth methods
- `Authorization: Bearer <token>` header (programmatic clients)
- `access_token` HTTP-only cookie (browser after login)
- The `get_current_user` dependency (`app/core/dependencies.py`) tries bearer first, falls back to cookie

## Auth endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/register/student` | Firebase token (opt) | Register student → JWT pair + cookies |
| POST | `/auth/register/recruiter` | Firebase token (opt) | Register recruiter → JWT pair + cookies |
| POST | `/auth/login` | Email/password or Firebase | Login → JWT pair + cookies |
| POST | `/auth/refresh` | Refresh token (body or cookie) | Rotate → new JWT pair + cookies |
| GET | `/auth/me` | Bearer or cookie | Bootstrap session; auto-refreshes if access token expired |
| POST | `/auth/logout` | Bearer or cookie + refresh | Blacklist tokens + clear cookies |

## Consistent error codes (`app/core/security.py` + `app/services/auth.py`)

| error_code | Cause | Where |
|-----------|-------|-------|
| `TOKEN_EXPIRED` | Access or refresh token past `exp` | `security.py` verify functions |
| `TOKEN_REUSED` | Refresh token already rotated/blacklisted | `auth.py` refresh_token |
| `TOKEN_INVALID` | Malformed, wrong type, bad signature | `security.py` verify functions |
| `USER_NOT_REGISTERED` | No user record found for token | `auth.py` get_user_by_token / login |
| `ACCOUNT_DISABLED` | User is_active=False | `auth.py` login / get_user_by_token / refresh_token |
| `NO_CREDENTIALS` | No bearer header and no cookie | `dependencies.py` get_current_user |
| `ROLE_MISMATCH` | Wrong role for protected endpoint | `dependencies.py` role guards |
| `USER_ALREADY_REGISTERED` | Duplicate email or firebase_uid | `auth.py` register methods |

## Token rotation

- Each access token and refresh token carries a unique `jti` (UUID) in its payload
- On `/auth/refresh`, the old refresh token is blacklisted with reason `rotated`
- A new access+refresh pair is issued (both with new jti values)
- Reusing a blacklisted refresh token returns `TOKEN_REUSED` (401)
- On `/auth/logout`, both the access and refresh tokens are blacklisted with reason `logout`

## Logging

All auth logs include a `request_id` (first 8 chars of UUID) for correlation:
```
[abc12345] POST /auth/login user_id=xyz role=student
```

The `RequestLoggingMiddleware` generates the request_id and stores it on `request.state.request_id`.

Rules:
- Always log: endpoint, user_id, role, error_code
- Never log: raw JWTs, refresh tokens, passwords, Firebase ID tokens

## CORS

CORSMiddleware must be the **last** middleware added (outermost) so error responses from `ErrorHandlerMiddleware` get CORS headers. Current order in `main.py`:

```
SecurityHeaders → RequestLogging → ErrorHandler → rate_limit → CORS
```

## Tests

```bash
pytest app/tests/ -v
```

- Tests mock `verify_firebase_token` — no real Firebase needed
- Tests mock `MongoAuthRepository` → `InMemoryAuthRepository` — no real MongoDB
- Tests mock `StudentRepository`/`RecruiterRepository` methods — no real Firestore
- Rate limiter disabled in tests via `os.environ["RATE_LIMIT_ENABLED"] = "false"`
- Test data is isolated per function (function-scoped fixtures)
- The `client` fixture in `conftest.py` uses `httpx.AsyncClient` with `ASGITransport`
- All auth endpoints are tested: register, login, refresh, /auth/me, logout, role guards

## Cookie configuration

Set these in `.env` for production:
```
COOKIE_SECURE=true
COOKIE_SAMESITE=none
```

For local development (localhost, HTTP):
```
COOKIE_SECURE=false
COOKIE_SAMESITE=lax
```

## Key conventions

- All custom exceptions carry an optional `error_code` string via `app/core/exceptions.py`
- `ErrorHandlerMiddleware` includes `error_code` in JSON responses when present
- Registration saves user **before** login is ever called; both use `firebase_uid` to link
- JWT secrets (`JWT_SECRET_KEY`, `JWT_REFRESH_SECRET`) must be set in `.env`
- AuthService methods accept optional `request_id` for log correlation
- Every token includes `jti` for rotation tracking
