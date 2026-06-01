## PROJECT OVERVIEW
 
**VERIF-AI** is a hackathon project: an AI-powered credential verification platform.
Students upload resume + certificates + GitHub URL. Three AI agents analyze each in parallel.
Recruiters see a Trust Score (0–100) with the AI's full research trail.
 
**This repo:** FastAPI backend only.  
**Partner's repo:** `verif-ai-frontend` — React + Vite + Tailwind (DO NOT TOUCH).  
**Shared contract:** `contracts/` folder — read before every feature.
 
---
 
## TECH STACK
 
- **Language:** Python 3.11+
- **Framework:** FastAPI (async, always `async def`)
- **Database:** MongoDB Atlas via Motor (async driver)
- **ODM:** Beanie
- **File storage:** MongoDB GridFS (NO Supabase, NO S3)
- **Auth:** Firebase Admin SDK (verify JWT tokens from frontend)
- **AI:** google-generativeai — Gemini 1.5 Flash + Gemini 1.5 Pro Vision
- **PDF:** pdfplumber
- **OCR:** pytesseract + Pillow
- **GitHub:** PyGithub
- **Deploy:** Render.com
---
 
## PROJECT STRUCTURE
 
```
verif-ai-backend/
├── app/
│   ├── api/v1/         → HTTP layer only (auth, documents, analysis, verification)
│   ├── services/       → Business logic (resume_agent, certificate_agent, github_agent, orchestrator)
│   ├── models/         → Beanie ODM models (user, document, ai_result, research_log, verification)
│   ├── schemas/        → Pydantic v2 request/response schemas
│   ├── core/           → Config, DB connection, Firebase init, security utils
│   └── main.py         → FastAPI app entry point
├── contracts/          → API contract markdown files (READ BEFORE CODING)
├── tests/              → pytest tests
├── .env                → Never commit
├── requirements.txt
└── render.yaml         → Render deployment
```
 
---
 
## CODING STANDARDS
 
### Must Follow
- All endpoints: `async def` with `await` on all I/O
- All external calls (Gemini, GitHub): wrapped in `try/except` with fallback
- All env vars via `os.getenv()` or Pydantic `BaseSettings`
- All responses structured: `{"success": bool, "data": {}, "message": ""}`
- All agents must save `research_logs` — this is the core differentiator
### File Naming
- Models: `snake_case.py` matching collection name
- Services: `{feature}_agent.py` or `{feature}_service.py`
- Schemas: match the model they describe
- Tests: `test_{feature}.py`
### Imports Order
1. Standard library
2. Third-party (`fastapi`, `motor`, `beanie`, `pydantic`)
3. Local (`from app.core`, `from app.models`)
---
 
## THE THREE AI AGENTS
 
### Core Concept
Each agent follows this pattern:
```
File retrieval → Local pre-processing → Gemini API call (with web_search) → Parse JSON → Save result + research_logs
```
 
### Agent 1 — Resume (`services/resume_agent.py`)
- Retrieve PDF from GridFS → `pdfplumber` extract text
- Compute stylometrics locally: avg_sentence_len, type_token_ratio, burstiness
- Call Gemini Flash with web_search enabled
- Return: `{ai_text_probability, skill_inflation_score, timeline_score, overall_resume_trust, flags[], research_steps[]}`
### Agent 2 — Certificate (`services/certificate_agent.py`)
- For each file: detect type → PDF metadata OR image OCR + ELA
- **ELA (Error Level Analysis) is mandatory** — re-compress at Q95, diff the images, compute std dev
- Call Gemini Vision with image bytes + OCR text
- Return: `{forgery_probability, issuer_verified, visual_tampering_score, overall_cert_trust, flags[], research_steps[]}`
### Agent 3 — GitHub (`services/github_agent.py`)
- PyGithub: get profile, repos, commits, languages
- Compute: fork ratio, burst score, commit message quality score, readme-only repos count
- Call Gemini Flash with all signals + web_search
- Return: `{originality_score, skill_match_score, commit_authenticity_score, overall_github_trust, flags[], research_steps[]}`
### Orchestrator (`services/orchestrator.py`)
- Always `asyncio.gather()` — never sequential
- `return_exceptions=True` — don't fail if one agent fails
- Trust formula: `resume×0.40 + cert×0.35 + github×0.25`
---
 
## RESEARCH LOGS — NEVER SKIP THIS
 
Every Gemini reasoning step must be saved to MongoDB:
```python
{
    "result_id": ObjectId,
    "user_id": ObjectId,
    "agent_type": "resume | certificate | github",
    "logs": [
        {
            "step": 1,
            "thought": "What the AI was thinking",
            "action": "web_search",
            "query": "search query used",
            "sources": ["url1", "url2"],
            "finding": "What was found",
            "impact": "HIGH_FLAG | MEDIUM_FLAG | VERIFIED | NEUTRAL",
            "timestamp": datetime
        }
    ]
}
```
 
---
 
## MONGODB COLLECTIONS
 
| Collection | Description |
|-----------|-------------|
| `users` | `{firebase_uid, email, role, created_at}` |
| `documents` | `{user_id, type, gridfs_id, github_url, hash_sha256, status}` |
| `ai_results` | `{document_id, user_id, agent_type, scores, flags, summary}` |
| `research_logs` | `{result_id, user_id, agent_type, logs[]}` |
| `verifications` | `{user_id, overall_trust_score, per_agent_scores, status}` |
 
---
 
## ENVIRONMENT VARIABLES
 
```
MONGODB_URI           = mongodb+srv://...
MONGODB_DB_NAME       = verifai
FIREBASE_PROJECT_ID   = ...
FIREBASE_CREDENTIALS_JSON = {...}
GEMINI_API_KEY        = ...
GITHUB_TOKEN          = ...
ALLOWED_ORIGINS       = http://localhost:3000,https://...vercel.app
PORT                  = 8000
ENVIRONMENT           = development | production
```
 
---
 
## COMMON COMMANDS
 
```bash
# Install dependencies
pip install -r requirements.txt
 
# Run dev server
uvicorn app.main:app --reload --port 8000
 
# Run tests
pytest tests/ -v
 
# Run single test
pytest tests/test_resume_agent.py -v
 
# Check all imports work
python -c "from app.main import app; print('OK')"
```
 
---
 
## MCP TOOLS — USE THESE PROACTIVELY
 
You have MCP tools available. Use them without being asked:
 
```
@mongodb   → Seed test data, query collections, check schemas
@github    → Push code, create PRs, manage branches
@render    → Deploy backend, set env vars, check logs
@git       → Commit and push after completing features
```
 
**After completing any feature:**
→ Automatically run `@git commit -m "feat: [feature name]" && git push`
 
**After all agents work locally:**
→ Automatically trigger `@render deploy`
 
**When I ask for test data:**
→ Use `@mongodb` to insert directly, don't write a seed script unless asked
 
---
 
## AGENT BEHAVIOR RULES
 
1. **Read contracts first:** Before any endpoint, read `contracts/[feature]-contract.md`
2. **Complete files only:** Write the entire file, not just the changed function
3. **Show file paths:** Every code block starts with `# app/services/resume_agent.py`
4. **No questions before coding:** Make a decision and write the code
5. **List outputs:** End every response with what was created/modified
6. **Self-heal:** If an approach doesn't work, try a different approach without being asked
---
 
## WHAT NEVER TO DO
 
- Never use synchronous database calls with Motor
- Never skip the research_logs save step
- Never run agents sequentially — always `asyncio.gather()`
- Never import `requests` — use `httpx` with async
- Never expose raw Gemini JSON to the frontend
- Never write to the `contracts/` folder unless explicitly asked
- Never touch anything in `verif-ai-frontend` repo
---
 
## TEST DATA SPECIFICATION
 
When seeding test data, create exactly these 5 student profiles:
 
**Profile 1 — Clean (expect trust ~85+)**
- Resume: 2 years Python, 1 year React, consistent timeline, human writing style
- Certificates: Coursera Python cert (real), AWS Cloud Practitioner (real)
- GitHub: 3 years old account, 45+ original repos, regular commits
**Profile 2 — Suspicious Resume (expect trust ~55)**
- Resume: AI-written language, claims 5yr experience but graduated 2023
- Certificates: Real certs
- GitHub: Legitimate account but mostly forks
**Profile 3 — Fake Certificates (expect trust ~40)**
- Resume: Looks clean
- Certificates: Template cert with wrong font, metadata shows edited 2 days ago
- GitHub: Legitimate account
**Profile 4 — Copy-paste GitHub (expect trust ~35)**
- Resume: Looks clean
- Certificates: Looks real
- GitHub: New account (3 months), all repos cloned, no original commits
**Profile 5 — Everything Fake (expect trust <20)**
- Resume: 100% AI-generated, impossible timeline
- Certificates: Photoshopped, issuer doesn't exist
- GitHub: New account, README-only repos
---
