# VerifAI Backend

Authentication & authorization system using Firebase Auth, FastAPI, JWT, and RBAC.

## Quick Start

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API: http://localhost:8000
- Docs: http://localhost:8000/docs

## Tech Stack

- **FastAPI** - Async web framework
- **Firebase Auth** - Authentication
- **Firebase Firestore** - Database
- **JWT** - Access & Refresh tokens

For Postman testing guide, see [testing.md](testing.md).
