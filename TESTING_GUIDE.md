# VERIF-AI — Complete Testing Guide
### From Local Dev to Production — Every Endpoint, Every Edge Case

---

## 🛠️ TESTING TOOLS — USE THESE (Not Postman)

| Tool | Use For | Install |
|------|---------|---------|
| **Bruno** | REST API testing, save collections in git | https://www.usebruno.com/ |
| **Hoppscotch** | WebSocket + SSE testing, zero install | https://hoppscotch.io |
| **Thunder Client** | Quick tests inside VSCode | VSCode extension |
| **pytest-asyncio** | Automated backend tests | `pip install pytest-asyncio` |
| **LangSmith** | Trace + debug every agent step | https://smith.langchain.com |

**Why Bruno over Postman:**
<br>Fully free. Open-source. Stores collections as `.bru` files in your repo.
<br>Commit them. Your brother can import them. No account required.

---

## STEP 1 — SETUP TESTING ENVIRONMENT

### Create `.env.test`
```bash
MONGODB_URI=mongodb+srv://...   # Use a separate test Atlas cluster or same with test DB
MONGODB_DB_NAME=verifai_test    # Different DB name — never test on production data
FIREBASE_PROJECT_ID=your-id
FIREBASE_CREDENTIALS_JSON={"type":"service_account",...}
GEMINI_API_KEY=your-key
GITHUB_TOKEN=your-github-pat
BRAVE_API_KEY=your-brave-key
ENVIRONMENT=test
```

### Install All Test Dependencies
```bash
pip install pytest pytest-asyncio httpx mongomock-motor pytest-cov
```

### Create `tests/conftest.py`
```python
import pytest, os
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch

os.environ["ENVIRONMENT"] = "test"
os.environ["MONGODB_DB_NAME"] = "verifai_test"

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture
async def client():
    from app.main import app
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver"
    ) as c:
        yield c

@pytest.fixture
def valid_firebase_token():
    """Mock a valid Firebase JWT - never make real Firebase calls in tests"""
    with patch("app.core.firebase.verify_firebase_token") as mock:
        mock.return_value = {
            "uid": "test_student_uid",
            "email": "student@test.com",
            "role": "student"
        }
        yield mock

@pytest.fixture
def recruiter_firebase_token():
    with patch("app.core.firebase.verify_firebase_token") as mock:
        mock.return_value = {
            "uid": "test_recruiter_uid",
            "email": "recruiter@test.com",
            "role": "recruiter"
        }
        yield mock

@pytest.fixture
def mock_gemini_flash():
    """Mock Gemini API - don't burn credits or make real network calls"""
    with patch("langchain_google_genai.ChatGoogleGenerativeAI") as mock:
        instance = MagicMock()
        instance.ainvoke = AsyncMock(return_value=MagicMock(content="""
        {
          "ai_text_probability": 0.85,
          "skill_inflation_score": 70.0,
          "timeline_consistency_score": 30.0,
          "overall_resume_trust": 40.0,
          "flags": [{"type": "skill_inflation", "severity": "high", "detail": "test"}],
          "research_steps": [{"step": 1, "thought": "test", "action": "web_search",
                              "query": "test", "sources": [], "finding": "test",
                              "impact": "NEUTRAL", "timestamp": "2025-01-01T00:00:00Z",
                              "duration_ms": 100}],
          "summary": "Test summary"
        }
        """))
        mock.return_value = instance
        yield instance

@pytest.fixture
def mock_mongodb(mongomock_motor):
    """Use mongomock-motor for in-memory MongoDB in tests"""
    with patch("app.core.database.get_motor_client") as mock:
        mock.return_value = mongomock_motor
        yield mock

@pytest.fixture
def sample_resume_pdf():
    """Minimal valid PDF bytes for testing"""
    return b"%PDF-1.4\n1 0 obj\n<</Type /Catalog>>\nendobj\n%%EOF"

@pytest.fixture
def sample_cert_image():
    """Minimal valid JPEG bytes"""
    from PIL import Image
    import io
    img = Image.new("RGB", (800, 600), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()
```

---

## STEP 2 — PHASE-BY-PHASE TEST PLANS

### PHASE 1: Health Check
```python
# tests/test_health.py
import pytest

@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_mongodb_connection(client):
    response = await client.get("/health/db")
    assert response.status_code == 200
    assert response.json()["mongodb"] == "connected"

@pytest.mark.asyncio
async def test_firebase_connection(client):
    response = await client.get("/health/firebase")
    assert response.status_code == 200
```

**Bruno Collection: Health**
```
GET http://localhost:8000/health
Expected: 200 {"status": "healthy", "mongodb": "connected", "firebase": "connected"}

GET http://localhost:8000/docs
Expected: 200 (FastAPI auto-generated OpenAPI docs)
```

---

### PHASE 2: Authentication Tests

```python
# tests/test_auth.py
import pytest

@pytest.mark.asyncio
async def test_sync_new_user(client, valid_firebase_token):
    response = await client.post("/api/v1/auth/sync", json={
        "firebase_uid": "test_student_uid",
        "email": "student@test.com",
        "role": "student"
    }, headers={"Authorization": "Bearer fake_but_mocked_token"})
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["role"] == "student"

@pytest.mark.asyncio
async def test_sync_requires_auth(client):
    """No token = 401"""
    response = await client.post("/api/v1/auth/sync", json={
        "firebase_uid": "uid", "email": "e@e.com", "role": "student"
    })
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_invalid_role_rejected(client, valid_firebase_token):
    """Invalid role = 422"""
    response = await client.post("/api/v1/auth/sync", json={
        "firebase_uid": "uid", "email": "e@e.com", "role": "admin"
    }, headers={"Authorization": "Bearer token"})
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_get_me_returns_user(client, valid_firebase_token):
    response = await client.get("/api/v1/auth/me",
                                 headers={"Authorization": "Bearer token"})
    assert response.status_code == 200
    assert response.json()["data"]["email"] == "student@test.com"
```

**Bruno Collection: Auth**
```
# Test 1: Valid registration
POST http://localhost:8000/api/v1/auth/sync
Headers: Authorization: Bearer {{firebase_token}}
Body: {"firebase_uid": "uid1", "email": "test@test.com", "role": "student"}
Expected: 201 success

# Test 2: No token
POST http://localhost:8000/api/v1/auth/sync
Body: {"firebase_uid": "uid1", "email": "test@test.com", "role": "student"}
Expected: 401

# Test 3: Get current user
GET http://localhost:8000/api/v1/auth/me
Headers: Authorization: Bearer {{firebase_token}}
Expected: 200 with user object
```

---

### PHASE 3: File Upload Tests

```python
# tests/test_documents.py
import pytest, io

@pytest.mark.asyncio
async def test_upload_resume_pdf(client, valid_firebase_token, sample_resume_pdf):
    response = await client.post(
        "/api/v1/documents/upload",
        files={"file": ("resume.pdf", sample_resume_pdf, "application/pdf")},
        data={"type": "resume", "student_id": "test_student_uid"},
        headers={"Authorization": "Bearer token"}
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert "document_id" in data
    assert "hash_sha256" in data
    assert len(data["hash_sha256"]) == 64   # SHA-256 is 64 hex chars

@pytest.mark.asyncio
async def test_upload_certificate_image(client, valid_firebase_token, sample_cert_image):
    response = await client.post(
        "/api/v1/documents/upload",
        files={"file": ("cert.jpg", sample_cert_image, "image/jpeg")},
        data={"type": "certificate", "student_id": "test_student_uid"},
        headers={"Authorization": "Bearer token"}
    )
    assert response.status_code == 201

@pytest.mark.asyncio
async def test_oversized_file_rejected(client, valid_firebase_token):
    """Files > 10MB must be rejected"""
    big_file = b"x" * (11 * 1024 * 1024)  # 11 MB
    response = await client.post(
        "/api/v1/documents/upload",
        files={"file": ("big.pdf", big_file, "application/pdf")},
        data={"type": "resume", "student_id": "uid"},
        headers={"Authorization": "Bearer token"}
    )
    assert response.status_code == 400
    assert "too large" in response.json()["error"].lower()

@pytest.mark.asyncio
async def test_invalid_file_type_rejected(client, valid_firebase_token):
    """Executables must be rejected"""
    response = await client.post(
        "/api/v1/documents/upload",
        files={"file": ("malware.exe", b"MZ\x90\x00", "application/octet-stream")},
        data={"type": "resume", "student_id": "uid"},
        headers={"Authorization": "Bearer token"}
    )
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_github_url_submission(client, valid_firebase_token):
    response = await client.post(
        "/api/v1/documents/github",
        json={"github_url": "https://github.com/torvalds",
              "student_id": "test_student_uid"},
        headers={"Authorization": "Bearer token"}
    )
    assert response.status_code == 201
    assert response.json()["data"]["type"] == "github"

@pytest.mark.asyncio
async def test_invalid_github_url_rejected(client, valid_firebase_token):
    response = await client.post(
        "/api/v1/documents/github",
        json={"github_url": "https://not-github.com/user",
              "student_id": "uid"},
        headers={"Authorization": "Bearer token"}
    )
    assert response.status_code == 400
```

---

### PHASE 4: Individual Agent Node Tests

```python
# tests/test_resume_node.py
import pytest
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_resume_node_happy_path(mock_gemini_flash):
    from app.services.graph.resume_node import resume_agent_node
    state = {
        "student_id": "test",
        "resume_doc_id": "doc_id_123",
        "research_logs": [],
        "flags": [],
        "completed_agents": []
    }
    result = await resume_agent_node(state)

    assert "resume_result" in result
    res = result["resume_result"]
    assert 0 <= res["overall_resume_trust"] <= 100
    assert 0 <= res["ai_text_probability"] <= 1
    assert isinstance(res["flags"], list)
    assert isinstance(res["research_steps"], list)
    assert len(result["research_logs"]) > 0       # Logs must be written
    assert "resume" in result["completed_agents"]  # Must mark self complete

@pytest.mark.asyncio
async def test_resume_node_handles_gemini_timeout(mock_mongodb):
    """If Gemini times out, node must return a fallback result, not crash"""
    from app.services.graph.resume_node import resume_agent_node
    with patch("app.services.graph.resume_node.get_gemini_flash") as mock_llm:
        mock_llm.return_value.ainvoke = AsyncMock(side_effect=TimeoutError("Gemini timeout"))
        state = {"resume_doc_id": "doc_id", "research_logs": [], "flags": [], "completed_agents": []}
        result = await resume_agent_node(state)
        # Must not raise — must return fallback score
        assert "resume_result" in result
        assert result["resume_result"]["overall_resume_trust"] == 50  # Fallback neutral score

@pytest.mark.asyncio
async def test_certificate_node_runs_ela(sample_cert_image):
    """ELA analysis must always run on image certificates"""
    from app.services.tools.image_tools import error_level_analysis
    score = error_level_analysis(sample_cert_image)
    assert isinstance(score, float)
    assert score >= 0

@pytest.mark.asyncio
async def test_github_node_computes_burst_score():
    from app.services.tools.github_tools import compute_burst_score
    from datetime import datetime, timedelta
    dates = [datetime(2024, 1, 1) + timedelta(days=i*30) for i in range(10)]
    score = compute_burst_score(dates)
    assert score > 0  # Regular monthly commits = some stdev

@pytest.mark.asyncio
async def test_stylometry_burstiness():
    from app.services.tools.stylometry_tools import compute_burstiness
    ai_text = "The solution leverages advanced methodologies. The platform enables scalable outcomes. The system provides comprehensive frameworks."
    human_text = "I built this during college. It was my first React project and honestly kind of a mess. But it worked!"
    ai_score = compute_burstiness(ai_text)
    human_score = compute_burstiness(human_text)
    assert human_score > ai_score  # Human writing has more variation
```

---

### PHASE 5: Full LangGraph Pipeline Test

```python
# tests/test_graph.py
import pytest
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_full_graph_completes(mock_gemini_flash):
    """Full LangGraph pipeline runs to completion with all 3 agents"""
    from app.services.graph.graph_builder import app as langgraph_app

    initial_state = {
        "student_id": "test_student",
        "resume_doc_id": "resume_doc_123",
        "cert_doc_ids": ["cert_doc_456", "cert_doc_789"],
        "github_url": "https://github.com/testuser",
        "research_logs": [],
        "flags": [],
        "completed_agents": []
    }
    result = await langgraph_app.ainvoke(initial_state)

    assert result["overall_trust_score"] is not None
    assert 0 <= result["overall_trust_score"] <= 100
    assert result["verdict"] in ["AUTHENTIC", "FLAGGED", "SUSPICIOUS", "FAKE"]
    assert len(result["completed_agents"]) == 3
    assert "resume" in result["completed_agents"]
    assert "certificate" in result["completed_agents"]
    assert "github" in result["completed_agents"]
    assert len(result["research_logs"]) > 0

@pytest.mark.asyncio
async def test_cross_reference_node_detects_mismatch():
    """Cross-ref node must flag skill-GitHub mismatches"""
    from app.services.graph.cross_reference import cross_reference_node

    state = {
        "resume_result": {
            "skills_claimed": ["React", "Python", "Docker"],
            "overall_resume_trust": 60.0
        },
        "github_result": {
            "languages_used": ["Python"],  # No React, no Docker
            "overall_github_trust": 70.0
        },
        "cert_result": {"overall_cert_trust": 80.0},
        "research_logs": [],
        "flags": []
    }
    result = await cross_reference_node(state)

    assert "cross_ref_findings" in result
    skill_flags = [f for f in result["cross_ref_findings"]
                   if f["type"] == "skill_github_mismatch"]
    assert len(skill_flags) >= 2  # React and Docker not in GitHub

@pytest.mark.asyncio
async def test_trust_score_formula():
    """Trust formula: resume×0.40 + cert×0.35 + github×0.25"""
    from app.services.trust_score import calculate_trust_score
    score = calculate_trust_score(
        resume_score=80.0,
        cert_score=60.0,
        github_score=40.0
    )
    expected = 80*0.40 + 60*0.35 + 40*0.25
    assert abs(score - expected) < 0.01

@pytest.mark.asyncio
async def test_single_agent_failure_doesnt_crash_pipeline(mock_gemini_flash):
    """If GitHub agent fails, other two should still complete"""
    from app.services.graph.github_node import github_agent_node
    from app.services.graph.graph_builder import app as langgraph_app

    with patch("app.services.graph.github_node.github_agent_node",
               side_effect=Exception("GitHub API rate limited")):
        initial_state = {
            "student_id": "test",
            "resume_doc_id": "doc1",
            "cert_doc_ids": ["cert1"],
            "github_url": "https://github.com/user",
            "research_logs": [],
            "flags": [],
            "completed_agents": []
        }
        result = await langgraph_app.ainvoke(initial_state)
        # Still produces a score (github defaults to 50 on failure)
        assert result["overall_trust_score"] is not None
```

---

### PHASE 6: API Integration Tests

```python
# tests/test_analysis_api.py
import pytest

@pytest.mark.asyncio
async def test_start_analysis_returns_job_id(client, valid_firebase_token, mock_gemini_flash):
    response = await client.post(
        "/api/v1/analysis/start",
        json={
            "student_id": "test_uid",
            "resume_document_id": "doc_resume",
            "certificate_document_ids": ["doc_cert1"],
            "github_url": "https://github.com/testuser"
        },
        headers={"Authorization": "Bearer token"}
    )
    assert response.status_code == 202
    data = response.json()["data"]
    assert "job_id" in data
    assert "websocket_url" in data
    assert data["status"] == "analyzing"

@pytest.mark.asyncio
async def test_get_result_after_analysis(client, valid_firebase_token):
    response = await client.get(
        "/api/v1/analysis/result/test_uid",
        headers={"Authorization": "Bearer token"}
    )
    # Either 200 (result exists) or 404 (not yet analyzed)
    assert response.status_code in [200, 404]
    if response.status_code == 200:
        data = response.json()["data"]
        assert 0 <= data["overall_trust_score"] <= 100
        assert data["verdict"] in ["AUTHENTIC", "FLAGGED", "SUSPICIOUS", "FAKE"]

@pytest.mark.asyncio
async def test_recruiter_can_search_by_email(client, recruiter_firebase_token):
    response = await client.get(
        "/api/v1/verification/search?email=student@test.com",
        headers={"Authorization": "Bearer recruiter_token"}
    )
    assert response.status_code in [200, 404]

@pytest.mark.asyncio
async def test_student_cannot_access_recruiter_search(client, valid_firebase_token):
    """Student role should be denied recruiter endpoints"""
    response = await client.get(
        "/api/v1/verification/search?email=anyone@test.com",
        headers={"Authorization": "Bearer student_token"}
    )
    assert response.status_code == 403
```

---

### PHASE 7: WebSocket Testing (Use Hoppscotch)

WebSocket tests are best done manually with **Hoppscotch** (https://hoppscotch.io):

```
STEP 1: Start analysis job
POST http://localhost:8000/api/v1/analysis/start
Body: {
  "student_id": "test",
  "resume_document_id": "doc1",
  "certificate_document_ids": ["cert1"],
  "github_url": "https://github.com/torvalds"
}
→ Copy the job_id from response

STEP 2: Connect to WebSocket in Hoppscotch
URL: ws://localhost:8000/api/v1/analysis/stream/{job_id}?token=<firebase_jwt>

EXPECTED MESSAGE SEQUENCE:
Message 1: {"type": "thinking_token", "agent": "resume", "content": "Analyzing..."}
Message 2: {"type": "research_step_start", "data": {"step": 1, "tool": "web_search", ...}}
Message 3: {"type": "research_step_complete", "data": {"step": 1, "finding": "...", "sources": [...]}}
...
Message N: {"type": "analysis_complete", "data": {"trust_score": 42, "verdict": "FLAGGED"}}

WHAT TO CHECK:
✅ Messages arrive in correct order
✅ Each research step has: step, thought, action, query, sources, finding, impact
✅ impact is one of: HIGH_FLAG | MEDIUM_FLAG | VERIFIED | NEUTRAL
✅ Final message has trust_score between 0-100
✅ Connection closes gracefully after analysis_complete
✅ Connection closes with 401 if token is invalid
```

---

## STEP 3 — BRUNO COLLECTION SETUP

Save this folder structure in your repo:

```
verif-ai-backend/
└── bruno-collection/
    ├── bruno.json
    ├── environments/
    │   ├── local.bru
    │   └── production.bru
    ├── auth/
    │   ├── sync-user.bru
    │   └── get-me.bru
    ├── documents/
    │   ├── upload-resume.bru
    │   ├── upload-certificate.bru
    │   └── submit-github.bru
    ├── analysis/
    │   ├── start-analysis.bru
    │   ├── get-result.bru
    │   └── get-logs.bru
    └── verification/
        └── recruiter-search.bru
```

**environments/local.bru:**
```
vars {
  base_url: http://localhost:8000
  firebase_token: paste_your_firebase_jwt_here
  student_id: test_student_uid
}
```

**Example Bruno request (auth/sync-user.bru):**
```
meta {
  name: Sync User
  type: http
  seq: 1
}
post {
  url: {{base_url}}/api/v1/auth/sync
  body: json
  auth: bearer
}
auth:bearer {
  token: {{firebase_token}}
}
body:json {
  {
    "firebase_uid": "test_uid",
    "email": "test@test.com",
    "role": "student"
  }
}
assert {
  res.status: eq 201
  res.body.success: eq true
}
```

---

## STEP 4 — GETTING A FIREBASE JWT FOR TESTING

You need a real Firebase JWT to test protected endpoints. Get one easily:

```javascript
// Run this in browser console on your frontend app after login:
const user = firebase.auth().currentUser;
const token = await user.getIdToken();
console.log(token);
// Paste this into Bruno's {{firebase_token}} variable
```

Or use this Python script:
```python
# get_test_token.py — run once to get a token for Bruno
import requests

FIREBASE_API_KEY = "your-firebase-web-api-key"  # From Firebase Console

response = requests.post(
    f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}",
    json={"email": "test@test.com", "password": "testpassword123", "returnSecureToken": True}
)
print(response.json()["idToken"])
```

---

## STEP 5 — RUNNING ALL TESTS

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=app --cov-report=html
# Open htmlcov/index.html to see coverage

# Run only unit tests (fast, no network)
pytest tests/ -v -m "not integration"

# Run only a specific test file
pytest tests/test_graph.py -v

# Run only a specific test
pytest tests/test_graph.py::test_full_graph_completes -v

# Run tests and stop on first failure
pytest tests/ -x -v

# Run with LangSmith tracing enabled (see agent traces in dashboard)
LANGCHAIN_TRACING_V2=true pytest tests/test_graph.py -v
```

---

## STEP 6 — LANGGRAPH AGENT DEBUGGING (LangSmith)

When an agent behaves wrong, use LangSmith to see exactly what happened:

```python
# In your .env:
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=from-smith.langchain.com
LANGCHAIN_PROJECT=verif-ai-hackathon

# Now run your tests normally:
pytest tests/test_graph.py -v

# Go to https://smith.langchain.com → verif-ai-hackathon project
# You'll see a visual trace of every:
# - LLM prompt sent and response received
# - Tool call made (web search, GitHub API, etc.)
# - State transitions between nodes
# - Which node failed and why
# - How long each step took
```

This is invaluable for debugging why Agent 3 gave a wrong score, for example.

---

## STEP 7 — 5 TEST PROFILES TO SEED

Seed these into Firebase Firestore + MongoDB for testing:

```python
# scripts/seed_test_data.py
# Run via: python scripts/seed_test_data.py

TEST_PROFILES = [
    {
        "name": "Clean Student (expect trust 85+)",
        "email": "clean@test.com",
        "password": "test123456",
        "resume_file": "tests/fixtures/clean_resume.pdf",
        "certs": ["tests/fixtures/real_coursera_cert.jpg"],
        "github_url": "https://github.com/torvalds"
    },
    {
        "name": "AI Resume (expect trust 45-60)",
        "email": "ai_resume@test.com",
        "password": "test123456",
        "resume_file": "tests/fixtures/ai_generated_resume.pdf",
        "certs": ["tests/fixtures/real_cert.jpg"],
        "github_url": "https://github.com/genuine_user"
    },
    {
        "name": "Fake Certificate (expect trust 35-50)",
        "email": "fake_cert@test.com",
        "password": "test123456",
        "resume_file": "tests/fixtures/normal_resume.pdf",
        "certs": ["tests/fixtures/photoshopped_cert.jpg"],
        "github_url": "https://github.com/real_user"
    },
    {
        "name": "Ghost Portfolio (expect trust 25-40)",
        "email": "ghost@test.com",
        "password": "test123456",
        "resume_file": "tests/fixtures/normal_resume.pdf",
        "certs": ["tests/fixtures/real_cert.jpg"],
        "github_url": "https://github.com/fork_heavy_user"
    },
    {
        "name": "Everything Fake (expect trust <20)",
        "email": "fraud@test.com",
        "password": "test123456",
        "resume_file": "tests/fixtures/fully_ai_resume.pdf",
        "certs": ["tests/fixtures/template_forgery.jpg"],
        "github_url": "https://github.com/brand_new_user_no_commits"
    }
]
```

---

## STEP 8 — PRE-DEMO CHECKLIST

Run through this checklist before presenting to judges:

```
BACKEND HEALTH:
□ GET /health returns {"status": "healthy"}
□ MongoDB connection confirmed
□ Firebase connection confirmed
□ All 3 Gemini API calls work (test with one quick prompt)
□ GitHub API token not rate-limited (GET https://api.github.com/rate_limit)

AUTH FLOW:
□ Student can register and login
□ Recruiter can login
□ Protected routes reject missing/expired tokens

UPLOAD FLOW:
□ Resume PDF uploads to MongoDB GridFS
□ Certificate images upload to MongoDB GridFS
□ GitHub URL submits and saves

ANALYSIS FLOW:
□ POST /api/v1/analysis/start returns job_id
□ WebSocket stream connects and sends events
□ All 3 agents complete (check completed_agents has 3 items)
□ Trust score is a number between 0-100
□ Research logs are saved to Firestore

RECRUITER FLOW:
□ Recruiter can search student by email
□ Recruiter sees trust score + verdict
□ Research log panel shows all steps

DEMO PROFILES:
□ clean@test.com → score 85+ → AUTHENTIC
□ fraud@test.com → score <20 → FAKE
□ ai_resume@test.com → score 50-60 → FLAGGED
□ Backup screenshots ready if live demo fails

DEPLOYMENT:
□ Backend live on Render, health check passes
□ Frontend live on Vercel, login works
□ CORS configured for Vercel URL
□ Environment variables set on Render
□ 60-second demo video recorded as backup
```

---

*Test everything. Demo nothing that hasn't been tested. Your backup video saves you.*
