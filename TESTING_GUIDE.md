# VERIF-AI — Testing Guide (Bruno + pytest)
> Every endpoint gets a Bruno test. Every test has real data.
> Run Bruno tests IMMEDIATELY after each endpoint is built.

---

## TOOLS

| Tool | Install | Use For |
|------|---------|---------|
| **Bruno** | https://www.usebruno.com/ | REST endpoints |
| **Hoppscotch** | https://hoppscotch.io (web) | WebSocket stream |
| **pytest-asyncio** | `pip install pytest-asyncio` | Automated unit tests |
| **LangSmith** | https://smith.langchain.com | Agent step tracing |

---

## BRUNO SETUP

### Folder structure inside your repo
```
verif-ai-backend/
└── bruno-collection/
    ├── bruno.json
    ├── environments/
    │   ├── local.bru       ← use during development
    │   └── production.bru  ← use after Render deploy
    ├── auth/
    ├── documents/
    ├── analysis/
    ├── profile/
    ├── discover/
    └── verification/
```

### `bruno-collection/bruno.json`
```json
{ "version": "1", "name": "VERIF-AI API", "type": "collection" }
```

### `environments/local.bru`
```
vars {
  base_url: http://localhost:8000
  student_token: PASTE_FIREBASE_JWT_HERE
  recruiter_token: PASTE_RECRUITER_FIREBASE_JWT_HERE
  student_uid: priya_firebase_uid
  recruiter_uid: meera_firebase_uid
}
```

### How to get a Firebase JWT for Bruno
```bash
# Run this Python script once after seeding data:
# scripts/get_test_token.py
import requests

FIREBASE_WEB_API_KEY = "your-firebase-web-api-key"  # Firebase Console → Project Settings → Web API Key

def get_token(email, password):
    r = requests.post(
        f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}",
        json={"email": email, "password": password, "returnSecureToken": True}
    )
    return r.json()["idToken"]

print("STUDENT TOKEN:", get_token("priya@test.com", "Test1234!"))
print("RECRUITER TOKEN:", get_token("meera@techcorp.com", "Test1234!"))
```
Paste the tokens into `environments/local.bru`.

---

## PHASE 0: HEALTH TESTS

### Test immediately after `main.py` is running

**Bruno: GET /health**
```
GET {{base_url}}/health
Expected: 200
{
  "status": "healthy",
  "mongodb": "connected",
  "firebase": "connected"
}
```

**Bruno: GET /**
```
GET {{base_url}}/
Expected: 200
{"message": "VERIF-AI API", "docs": "/docs", "version": "1.0.0"}
```

**Manual check:** Open `http://localhost:8000/docs` in browser → Swagger UI must load.

---

## PHASE 1: AUTH TESTS

### Test after building `api/v1/auth.py`

**Bruno: POST /api/v1/auth/sync — new student**
```
POST {{base_url}}/api/v1/auth/sync
Headers: Authorization: Bearer {{student_token}}
Body JSON:
{
  "firebase_uid": "priya_test_uid_001",
  "email": "priya@test.com",
  "role": "student",
  "display_name": "Priya Sharma"
}

Expected: 201
{
  "success": true,
  "data": {
    "id": "...",
    "firebase_uid": "priya_test_uid_001",
    "email": "priya@test.com",
    "role": "student",
    "display_name": "Priya Sharma"
  },
  "message": "User created"
}
```

**Bruno: POST /api/v1/auth/sync — new recruiter**
```
POST {{base_url}}/api/v1/auth/sync
Headers: Authorization: Bearer {{recruiter_token}}
Body JSON:
{
  "firebase_uid": "meera_test_uid_002",
  "email": "meera@techcorp.com",
  "role": "recruiter",
  "display_name": "Meera Patel"
}
Expected: 201
```

**Bruno: POST /api/v1/auth/sync — sync again (should update, not duplicate)**
```
Same body as student above.
Expected: 200 (not 201 — already exists)
```

**Bruno: GET /api/v1/auth/me — valid token**
```
GET {{base_url}}/api/v1/auth/me
Headers: Authorization: Bearer {{student_token}}
Expected: 200 with student user object
```

**Bruno: GET /api/v1/auth/me — no token (should fail)**
```
GET {{base_url}}/api/v1/auth/me
No Authorization header.
Expected: 401 {"success": false, "error": "..."}
```

**Bruno: PUT /api/v1/auth/role — update to recruiter**
```
PUT {{base_url}}/api/v1/auth/role
Headers: Authorization: Bearer {{student_token}}
Body: {"role": "recruiter"}
Expected: 200 with updated role
```

---

## PHASE 2: DOCUMENT UPLOAD TESTS

### Test after building `api/v1/documents.py`

**Bruno: POST /api/v1/documents/upload — valid PDF resume**
```
POST {{base_url}}/api/v1/documents/upload
Headers: Authorization: Bearer {{student_token}}
Body: multipart/form-data
  file: [select any small PDF from your computer]
  type: resume

Expected: 201
{
  "success": true,
  "data": {
    "document_id": "some_objectid",
    "type": "resume",
    "hash_sha256": "64-character-hex-string",
    "status": "pending",
    "filename": "your_file.pdf"
  }
}
Save the document_id → use in analysis tests
```

**Bruno: POST /api/v1/documents/upload — valid JPEG certificate**
```
POST {{base_url}}/api/v1/documents/upload
Headers: Authorization: Bearer {{student_token}}
Body: multipart/form-data
  file: [any JPEG image]
  type: certificate

Expected: 201 with document_id
Save this certificate document_id too
```

**Bruno: POST /api/v1/documents/upload — too large (should fail)**
```
POST {{base_url}}/api/v1/documents/upload
Headers: Authorization: Bearer {{student_token}}
Body: multipart/form-data
  file: [a file > 10MB]
  type: resume

Expected: 400
{"success": false, "error": "File too large", "detail": "Maximum 10MB"}
```

**Bruno: POST /api/v1/documents/upload — wrong type (should fail)**
```
POST {{base_url}}/api/v1/documents/upload
Headers: Authorization: Bearer {{student_token}}
Body: multipart/form-data
  file: [any .exe or .zip file]
  type: resume

Expected: 400
{"success": false, "error": "Invalid file type"}
```

**Bruno: POST /api/v1/documents/github — valid URL**
```
POST {{base_url}}/api/v1/documents/github
Headers: Authorization: Bearer {{student_token}}
Body JSON:
{
  "github_url": "https://github.com/tejasM17",
  "student_uid": "priya_test_uid_001"
}

Expected: 201 with document_id
Save this github document_id
```

**Bruno: POST /api/v1/documents/github — invalid URL (should fail)**
```
Body JSON:
{
  "github_url": "https://gitlab.com/someone",
  "student_uid": "priya_test_uid_001"
}
Expected: 400 {"error": "Invalid GitHub URL"}
```

**Bruno: GET /api/v1/documents/my**
```
GET {{base_url}}/api/v1/documents/my
Headers: Authorization: Bearer {{student_token}}
Expected: 200 list of 3 documents (resume + certificate + github)
```

---

## PHASE 3: ANALYSIS TESTS

### Test after building `api/v1/analysis.py`

**Bruno: POST /api/v1/analysis/start**
```
POST {{base_url}}/api/v1/analysis/start
Headers: Authorization: Bearer {{student_token}}
Body JSON:
{
  "student_uid": "priya_test_uid_001",
  "resume_document_id": "PASTE_RESUME_DOC_ID_FROM_PHASE_2",
  "certificate_document_ids": ["PASTE_CERT_DOC_ID_FROM_PHASE_2"],
  "github_url": "https://github.com/tejasM17"
}

Expected: 202
{
  "success": true,
  "data": {
    "job_id": "some_uuid",
    "status": "analyzing",
    "websocket_url": "/api/v1/analysis/stream/some_uuid"
  }
}
Save job_id
```

**Hoppscotch: WebSocket Test**
```
1. Open https://hoppscotch.io
2. Click "Realtime" → "WebSocket"
3. URL: ws://localhost:8000/api/v1/analysis/stream/YOUR_JOB_ID?token=YOUR_STUDENT_TOKEN
4. Click Connect
5. Watch messages appear in sequence:
   {"type": "thinking_token", "agent": "resume", "content": "..."}
   {"type": "research_step_start", "data": {"step": 1, "tool": "web_search", ...}}
   {"type": "research_step_complete", "data": {"finding": "...", "sources": [...], "impact": "..."}}
   ...
   {"type": "analysis_complete", "data": {"trust_score": 88, "verdict": "AUTHENTIC"}}

CHECK:
✅ Messages arrive in order
✅ Each step has: step, thought, action, sources, finding, impact
✅ impact is one of: HIGH_FLAG | MEDIUM_FLAG | VERIFIED | NEUTRAL
✅ Final message has trust_score 0-100
✅ Connection closes after analysis_complete
```

**Bruno: GET /api/v1/analysis/result/{student_uid}**
```
GET {{base_url}}/api/v1/analysis/result/priya_test_uid_001
Headers: Authorization: Bearer {{student_token}}
Expected: 200 with full verification result including all 3 agent scores
```

---

## PHASE 4: DISCOVERY TESTS

### Test after building profile + discover endpoints

**Bruno: PUT /api/v1/profile/update — add skills**
```
PUT {{base_url}}/api/v1/profile/update
Headers: Authorization: Bearer {{student_token}}
Body JSON:
{
  "skills": ["Python", "FastAPI", "MongoDB", "Machine Learning"],
  "domain": "Backend Development",
  "location": "Bangalore, India",
  "bio": "Final year ECE student at Srinivas Institute of Technology",
  "is_public": false
}
Expected: 200 with updated profile
```

**Bruno: POST /api/v1/profile/publish — make discoverable**
```
POST {{base_url}}/api/v1/profile/publish
Headers: Authorization: Bearer {{student_token}}
Expected: 200 {"success": true, "message": "Profile is now public"}
```

**Bruno: GET /api/v1/profile/{uid} — public**
```
GET {{base_url}}/api/v1/profile/priya_test_uid_001
No auth header needed (public endpoint)
Expected: 200 with PublicProfile (trust_score visible)
```

**Bruno: GET /api/v1/discover — browse all**
```
GET {{base_url}}/api/v1/discover
Headers: Authorization: Bearer {{recruiter_token}}
Expected: 200 with list of public verified students sorted by trust_score desc
```

**Bruno: GET /api/v1/discover/search — filter by skills**
```
GET {{base_url}}/api/v1/discover/search?skills=Python&min_trust=70
Headers: Authorization: Bearer {{recruiter_token}}
Expected: 200 with only students with Python skill AND trust_score >= 70
Priya (88) should appear. Faisal (18) should NOT appear.
```

**Bruno: GET /api/v1/discover/search — filter by domain**
```
GET {{base_url}}/api/v1/discover/search?domain=Backend%20Development
Headers: Authorization: Bearer {{recruiter_token}}
Expected: students in Backend Development domain
```

**Bruno: POST /api/v1/discover/shortlist/{uid}**
```
POST {{base_url}}/api/v1/discover/shortlist/priya_test_uid_001
Headers: Authorization: Bearer {{recruiter_token}}
Expected: 200 {"success": true, "message": "Student shortlisted"}
```

**Bruno: GET /api/v1/discover/shortlist**
```
GET {{base_url}}/api/v1/discover/shortlist
Headers: Authorization: Bearer {{recruiter_token}}
Expected: 200 with Priya's profile in the list
```

**Bruno: GET /api/v1/discover — student trying (should fail)**
```
GET {{base_url}}/api/v1/discover
Headers: Authorization: Bearer {{student_token}}
Expected: 403 {"error": "Recruiters only"}
```

**Bruno: GET /api/v1/verification/student/{uid} — recruiter views student**
```
GET {{base_url}}/api/v1/verification/student/priya_test_uid_001
Headers: Authorization: Bearer {{recruiter_token}}
Expected: 200 with full verification result
```

---

## FULL END-TO-END TEST (Run Before Demo)

Run these 8 steps in order, no skipping:

```
1. GET /health → {"status": "healthy"}
2. POST /auth/sync (student) → 201 user created
3. POST /documents/upload (resume PDF) → 201 document_id A
4. POST /documents/upload (cert image) → 201 document_id B
5. POST /documents/github (URL) → 201 document_id C
6. POST /analysis/start (A, B, C) → 202 job_id D
7. WebSocket stream/{D} → watch all messages → "analysis_complete" received
8. GET /discover/search?min_trust=0 → student appears in results
```

All 8 must succeed. If any fails, don't proceed to demo.

---

## DEMO ACCOUNTS (After running seed_fake_data.py)

| Name | Email | Password | Role | Trust Score | Demo Use |
|------|-------|----------|------|------------|---------|
| Priya Sharma | priya@test.com | Test1234! | student | 88 | Show AUTHENTIC result |
| Rahul Mehta | rahul@test.com | Test1234! | student | 55 | Show FLAGGED result |
| Anjali Singh | anjali@test.com | Test1234! | student | 42 | Show fake cert detection |
| Vikram Nair | vikram@test.com | Test1234! | student | 33 | Show ghost GitHub |
| Faisal Khan | faisal@test.com | Test1234! | student | 18 | Show FAKE result |
| Meera Patel | meera@techcorp.com | Test1234! | recruiter | — | Show recruiter dashboard |
| Arjun Reddy | arjun@startupx.com | Test1234! | recruiter | — | Show search/shortlist |

**Demo script:**
1. Login as Faisal (fake) → show Trust Score 18, FAKE verdict, research logs
2. Login as Priya (clean) → show Trust Score 88, AUTHENTIC, research logs
3. Login as Meera (recruiter) → search "Python min_trust=70" → Priya appears → shortlist her
4. Show Priya's shareable link → open in incognito → trust score visible publicly

---

## PYTEST RUN COMMANDS

```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=app --cov-report=html
# View: open htmlcov/index.html

# One phase only
pytest tests/test_auth.py tests/test_documents.py -v

# Stop on first failure
pytest tests/ -x -v

# With LangSmith tracing (see agent thoughts in dashboard)
LANGCHAIN_TRACING_V2=true pytest tests/test_graph.py -v
```
