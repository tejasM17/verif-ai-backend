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
| Database | Firestore (via `google-cloud-firestore`) | `app/database/session.py`, `app/repositories/base.py` |
| JWT | `python-jose[cryptography]` HS256 | `app/core/security.py` |
| API | FastAPI | `app/api/auth.py`, `app/main.py` |

- Firebase project ID: `verifai111` (`app/config/settings.py:12`)
- Users stored in Firestore collections: `students`, `recruiters`
- Lookup key is `firebase_uid` (not email), consistent across register and login
- Service account resolved from `firebase-service-account.json` (file) or `.env` vars (fallback)

## Firebase token verification (`app/auth/firebase.py`)

`verify_firebase_token()` calls `auth.verify_id_token()`. Returns `error_code` in JSON for these cases:

| error_code | Cause |
|-----------|-------|
| `TOKEN_USED_TOO_EARLY` | Server clock out of sync with Firebase — check NTP |
| `FIREBASE_PROJECT_MISMATCH` | Token's `aud` differs from `settings.FIREBASE_PROJECT_ID` |
| `INVALID_FIREBASE_TOKEN` | Token is malformed, wrong format, or from wrong project |
| `TOKEN_EXPIRED` | Token past its `exp` claim |
| `TOKEN_REVOKED` | User's token revoked in Firebase Console |
| `USER_NOT_REGISTERED` | Token valid but no matching Firestore doc found (login only) |

## Auth flow

```
Client -> Firebase Auth SDK -> ID token -> POST /auth/student/register (or /auth/login)
                                           -> verify_firebase_token(id_token)
                                           -> lookup by firebase_uid in students/recruiters
                                           -> create JWT access+refresh tokens
                                           -> return to client
```

- `POST /auth/student/register` and `POST /auth/recruiter/register` — register + return JWT
- `POST /auth/login` — verify token → lookup in `students` (by `firebase_uid`) → `recruiters` (by `firebase_uid`) → fail with `error_code: USER_NOT_REGISTERED`
- `POST /auth/refresh` — exchange refresh token for new access+refresh pair
- `POST /auth/logout` — blacklists both tokens in `token_blacklist` collection

## CORS

CORSMiddleware must be the **last** middleware added (outermost) so error responses from `ErrorHandlerMiddleware` get CORS headers. Current order in `main.py`:

```
SecurityHeaders → RequestLogging → ErrorHandler → rate_limit → CORS
```

## Tests
if new end point is added then update that endpoint in testing.md file

```bash
pytest app/tests/ -v
```

Tests mock `verify_firebase_token` — no real Firebase needed. The `client` fixture in `conftest.py` uses `httpx.AsyncClient` with `ASGITransport`.

## Debugging token issues

Check server clock on the FastAPI host:

```bash
# Windows
w32tm /query /status
# Linux
chronyc tracking
```

Backend logs the server time in every `verify_firebase_token` call:
```
Server time at token verification: 2026-06-06T12:00:00+00:00 (epoch=1234567890.000)
```

If you see `TOKEN_USED_TOO_EARLY`, the **server** clock is ahead of Firebase's clock. Sync with NTP.

## Key conventions

- All custom exceptions carry an optional `error_code` string via `app/core/exceptions.py`
- `ErrorHandlerMiddleware` includes `error_code` in JSON responses when present
- Registration saves user **before** login is ever called; both use `firebase_uid` to link
- JWT secrets (`JWT_SECRET_KEY`, `JWT_REFRESH_SECRET`) must be set in `.env`
