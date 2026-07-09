# VerifAI Backend

FastAPI authentication backend with Firebase email/password login.

## Setup

```bash
python -m venv venv
source venv/bin/activate       # Linux / macOS
# venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Place your Firebase Admin SDK key as `firebase-key.json` in this directory.

## Run

```bash
uvicorn main:app --reload
```

## Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/signup` | No | Create account (email, password) |
| POST | `/login` | No | Login, returns idToken |
| GET | `/me` | Bearer | Get profile from token |
| GET | `/` | No | Health check |

## Example Requests

```bash
# Signup
curl -X POST http://localhost:8000/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secret123"}'

# Login
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secret123"}'

# Protected route
curl http://localhost:8000/me \
  -H "Authorization: Bearer <idToken>"
```

## Firebase Setup

1. Go to Firebase Console → Project Settings → Service Accounts
2. Generate new private key → save as `firebase-key.json`
3. Enable Email/Password sign-in in Authentication → Sign-in method
