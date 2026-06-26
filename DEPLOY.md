# VerifAI Backend — Deploy to Render

## One-time setup

1. Create a Render account at https://dashboard.render.com (sign in with GitHub recommended).
2. Push this repo to GitHub if you haven't already.
3. In Render Dashboard, click **New + → Blueprint**.
4. Connect the GitHub repo that contains `verif-ai-backend/`.
5. Render will detect `verif-ai-backend/render.yaml` and show the `verifai-backend` web service preview.
6. Apply — Render will create the service, build, and deploy.

## Setting environment variables

After the service is created, go to **Environment** in the Render dashboard and set:

| Variable | Value | Notes |
|---|---|---|
| `FIREBASE_WEB_API_KEY` | (copy from your local `.env`) | Firebase Web API key, used for password sign-in REST |
| `FIREBASE_CRED_PATH` | `firebase-key.json` | Already set in `render.yaml`. If you choose to inject credentials as a single env var instead, see "Firebase credentials" below. |
| `FIREBASE_DATABASE_URL` | (copy from your local `.env`) | Firebase RTDB URL |
| `MONGODB_URI` | (same connection string as local — Atlas allows IP 0.0.0.0/0) | The local `.env` connection string already points at your Atlas cluster, so the same value works in prod as long as Atlas network access is open. |
| `CORS_ORIGINS` | `https://your-vercel-app.vercel.app` (add after frontend deploy) | Comma-separated list. Leave as `http://localhost:3000` for first deploy, then update. |

### Firebase credentials

`firebase-key.json` is committed in your repo (visible to anyone with repo access). For a hackathon that's fine. For real production you should:

1. Add `firebase-key.json` to `.gitignore`.
2. Store the JSON contents as a Render Secret File (Render Dashboard → Environment → Secret Files) — the path will be e.g. `/etc/secrets/firebase-key.json`.
3. Update `FIREBASE_CRED_PATH` to that path.

For the hackathon demo, leaving the file in the repo is fine.

## Smoke test

After the first deploy completes (3-5 min for a cold build), grab the URL — Render assigns `https://verifai-backend.onrender.com` (or whatever name you gave the service).

```bash
# Health check
curl https://verifai-backend.onrender.com/

# Signup a test user (role is dropped per AGENTS.md known-gaps; set it via /profile/onboarding after)
curl -X POST https://verifai-backend.onrender.com/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"smoke@test.com","password":"hunter2!!"}'

# Log in
curl -X POST https://verifai-backend.onrender.com/login \
  -H "Content-Type: application/json" \
  -d '{"email":"smoke@test.com","password":"hunter2!!"}'

# Use the returned idToken
TOKEN="...paste here..."
curl https://verifai-backend.onrender.com/me \
  -H "Authorization: Bearer $TOKEN"
```

If those three calls return without 5xx, the backend is live.

## Atlas IP allowlist

The first deploy may fail with a Mongo connection timeout if Atlas is locked down. Go to MongoDB Atlas → Network Access → Add IP Address → **Allow Access from Anywhere** (`0.0.0.0/0`). Render's free tier uses dynamic IPs.

## CORS update after frontend deploy

Once the frontend is deployed (next doc), update `CORS_ORIGINS` in Render env vars to include the Vercel URL. The backend code reads this and replaces the hardcoded `allow_origins=["http://localhost:3000"]`. (See `backend/DEPLOY_CORS_NOTE.md` for the exact code change.)

Render will auto-redeploy on env var changes.

## URL you'll have

`https://verifai-backend.onrender.com` — copy this for the frontend `VITE_API_URL`.
