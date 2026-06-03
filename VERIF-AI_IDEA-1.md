# VERIF-AI — Complete Master Idea Document
### AI-Powered Academic Profile & Skill Verification System
#### Built with LangGraph Multi-Agent System + Google Gemini + Firebase + MongoDB

---

## 🎯 ONE-LINE PITCH

> **"VERIF-AI is a LangGraph-powered multi-agent verification platform where three specialized AI agents collaborate, debate, and collectively decide whether a student's resume, certificates, and GitHub code are genuine — giving recruiters a transparent, research-backed Trust Score with full AI reasoning trail."**

---

## 🔴 THE PROBLEM (Why This Matters Right Now)

The hiring pipeline is broken at the source:

| Fraud Type | Reality |
|-----------|---------|
| AI-generated resumes | 45%+ of applicants use AI tools to write resumes (2025) |
| Forged certificates | PDF editing takes 10 minutes, detection takes 3 days manually |
| Ghost portfolios | GitHub repos cloned, AI-written, or staged before job applications |
| Manual verification | Average recruiter spends 7 seconds per resume — fraud passes easily |

**No single tool today verifies all three simultaneously with explainable AI reasoning.**
VERIF-AI solves this in under 60 seconds.

---

## 🟢 WHAT YOU ARE BUILDING — Crystal Clear

A web platform where:

1. **Student uploads** → Resume PDF + Certificate images/PDFs + GitHub profile URL
2. **LangGraph Supervisor** → Receives all three, creates a shared verification state
3. **Three specialized LangGraph agents** → Run in parallel, each with their own tools and web search
4. **Agents communicate** → Each agent writes findings to shared state; others can reference them
5. **Supervisor aggregates** → Reads all agent findings, runs cross-checks, calculates final Trust Score
6. **Every thought is logged** → WebSocket streams live research steps to frontend in real-time
7. **Recruiter sees** → Trust Score + animated research log (like Grok/Perplexity) + exportable report

**What makes this unique:** The agents don't just run in isolation. They share state. The GitHub agent's findings influence how the Resume agent's timeline claims are re-evaluated. That cross-agent reasoning is your killer feature.

---

## 🏗️ SYSTEM ARCHITECTURE — LangGraph Multi-Agent

```
┌─────────────────────────────────────────────────────────────────┐
│                        STUDENT PORTAL                           │
│    Resume PDF  │  Certificate Images/PDFs  │  GitHub URL        │
└──────────────────────────┬──────────────────────────────────────┘
                           │ POST /api/v1/analysis/start
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                               │
│                  Firebase JWT Auth                               │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              LANGGRAPH SUPERVISOR NODE                          │
│   • Creates shared VerificationState                            │
│   • Dispatches to all 3 agents in parallel                      │
│   • Monitors completion, runs cross-checks                      │
│   • Calculates final Trust Score                                │
└──────┬──────────────────┬─────────────────────┬────────────────┘
       │                  │                      │
       ▼                  ▼                      ▼
┌─────────────┐  ┌─────────────────┐  ┌──────────────────┐
│  RESUME     │  │  CERTIFICATE    │  │  GITHUB          │
│  AGENT      │  │  AGENT          │  │  AGENT           │
│  NODE       │  │  NODE           │  │  NODE            │
│             │  │                 │  │                  │
│ Tools:      │  │ Tools:          │  │ Tools:           │
│ • PDF parse │  │ • OCR           │  │ • GitHub API     │
│ • stylometry│  │ • ELA forensics │  │ • Commit OSINT   │
│ • web search│  │ • PDF metadata  │  │ • Code analysis  │
│ • timeline  │  │ • web search    │  │ • web search     │
│   checker   │  │ • issuer verify │  │ • fork detector  │
│             │  │                 │  │                  │
│ Writes to:  │  │ Writes to:      │  │ Writes to:       │
│ State.resume│  │ State.certs     │  │ State.github     │
└──────┬──────┘  └────────┬────────┘  └────────┬─────────┘
       │                  │                      │
       └──────────────────┴──────────────────────┘
                           │ All 3 write to shared state
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              CROSS-REFERENCE NODE (LangGraph Edge)              │
│   • GitHub commits vs Resume timeline claims                    │
│   • Certificate course vs GitHub language evidence              │
│   • Resume company claims vs web search verification            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FINAL DECISION NODE                          │
│   trust_score = resume×0.40 + cert×0.35 + github×0.25          │
│   verdict: AUTHENTIC | FLAGGED | SUSPICIOUS | FAKE             │
└──────────────────────────┬──────────────────────────────────────┘
                           │ WebSocket stream throughout
                           ▼
┌────────────────────────────────────────────────────────────────┐
│                   STORAGE LAYER                                │
│  Firebase Firestore → users, ai_results, verifications         │
│  MongoDB GridFS    → resume PDFs, certificate images/PDFs      │
│  Firebase Auth     → all authentication                        │
└────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    RECRUITER DASHBOARD                          │
│  Trust Score gauge │ Animated research log │ PDF export        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧠 LANGGRAPH — WHY IT FITS PERFECTLY

### LangChain vs LangGraph — The Right Choice for VERIF-AI

| Scenario | Use LangChain | Use LangGraph |
|---------|--------------|--------------|
| Simple chatbot | ✅ | Overkill |
| Single agent Q&A | ✅ | Overkill |
| **Multi-agent system** | ❌ Gets messy | **✅ Built for this** |
| **Shared state across agents** | ❌ No built-in | **✅ StateGraph** |
| **Conditional routing** | ❌ Hard | **✅ Conditional edges** |
| **Loops + iterative refinement** | ❌ Manual | **✅ Native** |
| **Agent-to-agent communication** | ❌ Hack | **✅ Shared state** |

VERIF-AI needs agents to **share findings with each other**. LangGraph's StateGraph is the exact tool for this. The GitHub agent's commit date findings feed directly into the Resume agent's timeline re-evaluation. That's only possible with LangGraph shared state.

### The LangGraph StateGraph Pattern for VERIF-AI

```python
from typing import TypedDict, Optional, Annotated
from langgraph.graph import StateGraph, END
import operator

# THE SHARED STATE — this is the "brain" all agents read/write
class VerificationState(TypedDict):
    # Input
    student_id: str
    resume_doc_id: str
    cert_doc_ids: list[str]
    github_url: str

    # Agent outputs (each agent writes here)
    resume_result: Optional[dict]
    cert_result: Optional[dict]
    github_result: Optional[dict]

    # Cross-reference findings
    cross_ref_findings: Optional[dict]

    # Research logs — accumulate across all agents
    # Annotated[list, operator.add] means: append, don't replace
    research_logs: Annotated[list[dict], operator.add]

    # Final output
    overall_trust_score: Optional[float]
    verdict: Optional[str]
    flags: Annotated[list[dict], operator.add]
    completed_agents: Annotated[list[str], operator.add]

# BUILD THE GRAPH
workflow = StateGraph(VerificationState)

# ADD NODES (each is a function or agent)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("resume_agent", resume_agent_node)
workflow.add_node("certificate_agent", certificate_agent_node)
workflow.add_node("github_agent", github_agent_node)
workflow.add_node("cross_reference", cross_reference_node)
workflow.add_node("final_decision", final_decision_node)

# ADD EDGES (flow control)
workflow.set_entry_point("supervisor")
workflow.add_edge("supervisor", "resume_agent")
workflow.add_edge("supervisor", "certificate_agent")
workflow.add_edge("supervisor", "github_agent")

# Conditional edge: only proceed when ALL 3 agents complete
workflow.add_conditional_edges(
    "resume_agent",
    lambda state: "cross_reference" if len(state["completed_agents"]) == 3 else "wait",
    {"cross_reference": "cross_reference", "wait": END}
)
workflow.add_edge("cross_reference", "final_decision")
workflow.add_edge("final_decision", END)

app = workflow.compile()
```

---

## 🔐 AUTHENTICATION & DATA STORAGE — STRICT RULES

### Firebase = Everything Auth + User Data

Firebase handles ALL authentication and user-related data:

```
Firebase Auth:
  ├── Email/Password login
  ├── Google OAuth login
  └── JWT tokens (passed to FastAPI as Bearer token)

Firebase Firestore:
  ├── users/{uid}               → profile, role, created_at
  ├── ai_results/{id}           → scores, flags, summary per agent
  ├── research_logs/{id}        → full step-by-step AI trail
  └── verifications/{id}        → final trust score + verdict
```

### MongoDB = ONLY File Storage (GridFS)

MongoDB's only job is storing binary files:

```
MongoDB GridFS:
  ├── resumes bucket     → resume PDFs (binary)
  ├── certificates bucket → certificate images + PDFs (binary)
  └── documents collection → metadata: filename, hash, firebase_uid, gridfs_id
```

**Why this split?**
- Firebase Firestore is better for structured data with real-time updates
- MongoDB GridFS is better for large binary files (PDFs, images)
- Firebase Auth is battle-tested and free — don't reinvent it
- This is cleaner, faster, and simpler than putting everything in MongoDB

### Firestore Schema

```
/users/{firebase_uid}
{
  "email": "student@example.com",
  "role": "student | recruiter",
  "display_name": "string",
  "created_at": "timestamp"
}

/ai_results/{result_id}
{
  "student_uid": "firebase_uid",
  "agent_type": "resume | certificate | github",
  "trust_score": 82.5,
  "ai_text_probability": 0.23,
  "forgery_score": 12.0,
  "flags": [{"type": "skill_inflation", "severity": "high", "detail": "..."}],
  "summary": "Plain English verdict",
  "created_at": "timestamp"
}

/research_logs/{log_id}
{
  "result_id": "ai_results doc id",
  "student_uid": "firebase_uid",
  "agent_type": "resume | certificate | github",
  "status": "running | complete | failed",
  "logs": [
    {
      "step": 1,
      "thought": "Checking if TechCorp Solutions existed before 2017...",
      "action": "web_search",
      "query": "TechCorp Solutions Bangalore founded year",
      "sources": ["https://linkedin.com/company/techcorp"],
      "finding": "Founded 2019 — timeline claim impossible",
      "impact": "HIGH_FLAG",
      "timestamp": "ISO8601",
      "duration_ms": 1240
    }
  ],
  "summary_stats": {
    "total_steps": 8, "high_flags": 2,
    "sources_visited": ["linkedin.com", "github.com"],
    "total_duration_ms": 14200
  }
}

/verifications/{verification_id}
{
  "student_uid": "firebase_uid",
  "overall_trust_score": 42.5,
  "verdict": "FLAGGED",
  "resume_score": 38.0,
  "cert_score": 61.0,
  "github_score": 30.0,
  "cross_ref_flags": [...],
  "created_at": "timestamp",
  "expires_at": "timestamp"
}
```

### MongoDB Schema (Files Only)

```
documents collection:
{
  "_id": ObjectId,
  "firebase_uid": "string",
  "type": "resume | certificate",
  "gridfs_id": ObjectId,
  "filename": "string",
  "mime_type": "application/pdf | image/jpeg | image/png",
  "hash_sha256": "string",
  "size_bytes": number,
  "status": "pending | analyzing | done | failed",
  "uploaded_at": ISODate
}
```

---

## 🤖 THE THREE LANGGRAPH AGENT NODES

### Agent Node 1 — Resume Analyzer

**What it does (step by step):**
1. Retrieve PDF from MongoDB GridFS → extract text with `pdfplumber`
2. Compute stylometrics locally (no API): avg sentence length, type-token ratio, burstiness score
3. Extract structure: skills[], education[], experience[], timeline[]
4. LangGraph node calls Gemini 1.5 Flash with web search tool
5. For every company claimed → web search → verify existence + founding date
6. For every skill claimed → web search → cross-reference with GitHub findings from shared state
7. Write findings + research steps to `VerificationState.resume_result`
8. Append all research steps to `VerificationState.research_logs`

**Key signal — Burstiness:**
Human writing has variable complexity (high burstiness). AI writing is uniformly smooth (low burstiness). This is measurable without any API call — pure Python.

```python
import statistics
def compute_burstiness(text: str) -> float:
    sentences = text.split('.')
    lengths = [len(s.split()) for s in sentences if s.strip()]
    if len(lengths) < 2:
        return 0.0
    mean = statistics.mean(lengths)
    std = statistics.stdev(lengths)
    return std / mean if mean > 0 else 0.0
# Human avg: 0.85+ | AI avg: 0.23 or lower
```

**Output written to state:**
```python
state["resume_result"] = {
    "ai_text_probability": 0.87,
    "skill_inflation_score": 72.0,
    "timeline_consistency_score": 25.0,
    "overall_resume_trust": 38.0,
    "flags": [...],
    "summary": "Resume shows strong AI generation signals..."
}
```

---

### Agent Node 2 — Certificate Verifier

**What it does:**
1. Retrieve each certificate from MongoDB GridFS
2. Detect file type → route to PDF pipeline or Image pipeline
3. **Image pipeline:** pytesseract OCR → extract text + run ELA (Error Level Analysis)
4. **PDF pipeline:** pypdf metadata extraction → check creation/modification dates
5. Gemini Vision: send image + OCR text → check if template matches real institution
6. Web search: does this institution actually issue this certificate?
7. Write findings to `VerificationState.cert_result`

**ELA — The key forensics tool:**
```python
from PIL import Image, ImageChops, ImageEnhance
import numpy as np, io

def error_level_analysis(image_bytes: bytes, quality: int = 95) -> float:
    """Higher return value = more editing detected = more suspicious"""
    original = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    buffer = io.BytesIO()
    original.save(buffer, "JPEG", quality=quality)
    recompressed = Image.open(buffer).convert("RGB")
    diff = ImageChops.difference(original, recompressed)
    enhanced = ImageEnhance.Brightness(diff).enhance(20)
    return float(np.std(np.array(enhanced)))
    # Score > 15 = suspicious editing detected
```

---

### Agent Node 3 — GitHub Code Verifier (Deep Agent)

**This is the most powerful agent — treats GitHub as a crime scene.**

**What it does:**
1. Extract username from URL → PyGithub → fetch complete profile
2. Compute repository intelligence: fork ratio, languages, readme-only count
3. Compute commit intelligence: burst score, commit message quality, timezone patterns
4. Extract top 5 repo code samples → compute complexity with `radon`
5. OSINT: extract commit emails → check for multiple identities
6. Gemini + web search: does GitHub story match resume claims?
7. **Critical cross-reference:** Read `state["resume_result"]` — compare claimed skills with actual GitHub language usage
8. Write findings to `VerificationState.github_result`

**Commit burst score:**
```python
import statistics
from datetime import datetime

def compute_burst_score(commit_dates: list[datetime]) -> float:
    """Low score = suspicious cramming. High = consistent real developer."""
    if len(commit_dates) < 2:
        return 0.0
    gaps = [(commit_dates[i+1]-commit_dates[i]).days
            for i in range(len(commit_dates)-1)]
    return statistics.stdev(gaps) if len(gaps) > 1 else 0.0
```

**Commit message quality:**
```python
def analyze_commit_quality(messages: list[str]) -> float:
    """Real devs write 'fix race condition in auth' not 'update' or 'asdf'"""
    learning_keywords = ["fix", "bug", "refactor", "revert", "debug", "wip", "test"]
    generic_keywords = ["update", "edit", "commit", "change", "asdf", "done", "aaa"]
    real_count = sum(1 for m in messages if any(k in m.lower() for k in learning_keywords))
    generic_count = sum(1 for m in messages if any(k in m.lower() for k in generic_keywords))
    return real_count / max(len(messages), 1) - (generic_count / max(len(messages), 1))
```

---

### The Cross-Reference Node — What Makes VERIF-AI Unique

This LangGraph node runs AFTER all 3 agents complete. It reads all three results from shared state and performs cross-agent analysis:

```python
async def cross_reference_node(state: VerificationState) -> dict:
    """
    This node only exists because of LangGraph's shared state.
    It cross-references findings across all 3 agents.
    """
    cross_findings = []

    # Cross-check 1: GitHub languages vs Resume skills
    resume_skills = extract_skills(state["resume_result"])
    github_languages = state["github_result"]["languages_used"]
    for skill in resume_skills:
        if skill not in github_languages:
            cross_findings.append({
                "type": "skill_github_mismatch",
                "detail": f"Resume claims {skill} but no GitHub repos use it",
                "severity": "high"
            })

    # Cross-check 2: Resume dates vs GitHub first commit dates
    resume_start_dates = extract_start_dates(state["resume_result"])
    github_first_commits = state["github_result"]["first_commits_by_language"]
    for lang, resume_date in resume_start_dates.items():
        github_date = github_first_commits.get(lang)
        if github_date and github_date > resume_date:
            cross_findings.append({
                "type": "timeline_github_mismatch",
                "detail": f"First {lang} commit on GitHub is AFTER claimed experience start date",
                "severity": "high"
            })

    # Cross-check 3: Certificate course vs GitHub evidence
    cert_courses = extract_cert_courses(state["cert_result"])
    for course in cert_courses:
        if not has_github_evidence(course, github_languages):
            cross_findings.append({
                "type": "cert_no_github_evidence",
                "detail": f"Certified in {course} but no GitHub projects demonstrate it",
                "severity": "medium"
            })

    state["research_logs"].append({
        "step": "cross_reference",
        "agent": "supervisor",
        "findings": cross_findings,
        "timestamp": datetime.utcnow().isoformat()
    })
    return {"cross_ref_findings": cross_findings}
```

---

## 📁 EXACT FOLDER STRUCTURE

```
verif-ai-backend/
├── GEMINI.md                           ← Gemini CLI reads this
├── AGENTS.md                           ← OpenCode reads this
├── app/
│   ├── api/v1/
│   │   ├── auth.py                     # Firebase JWT verify + user sync to Firestore
│   │   ├── documents.py                # MongoDB GridFS upload
│   │   ├── analysis.py                 # Trigger LangGraph + WebSocket stream
│   │   └── verification.py             # Get results + recruiter search
│   ├── services/
│   │   ├── graph/
│   │   │   ├── state.py                # VerificationState TypedDict
│   │   │   ├── supervisor.py           # Supervisor node
│   │   │   ├── resume_node.py          # Resume agent node
│   │   │   ├── certificate_node.py     # Certificate agent node
│   │   │   ├── github_node.py          # GitHub agent node (Deep Agent)
│   │   │   ├── cross_reference.py      # Cross-reference node
│   │   │   ├── final_decision.py       # Trust score + verdict node
│   │   │   └── graph_builder.py        # StateGraph assembly
│   │   ├── tools/
│   │   │   ├── pdf_tools.py            # pdfplumber + pypdf tools
│   │   │   ├── image_tools.py          # pytesseract + ELA tools
│   │   │   ├── github_tools.py         # PyGithub tools
│   │   │   └── stylometry_tools.py     # Burstiness, TTR, readability
│   │   ├── streaming.py                # astream_events v3 → WebSocket
│   │   └── trust_score.py              # Weighted formula
│   ├── core/
│   │   ├── database.py                 # MongoDB Motor + GridFS
│   │   ├── firebase.py                 # Firebase Admin + Firestore client
│   │   ├── config.py                   # Pydantic BaseSettings
│   │   └── langchain_setup.py          # Gemini LLM factory + LangSmith
│   └── main.py
├── contracts/
│   ├── CONTRACT.md                     ← Auto-updated API contract
│   ├── resume-agent.md                 # System prompt
│   ├── certificate-agent.md
│   └── github-agent.md
├── tests/
│   ├── conftest.py                     # Shared fixtures
│   ├── test_auth.py
│   ├── test_documents.py
│   ├── test_resume_node.py
│   ├── test_certificate_node.py
│   ├── test_github_node.py
│   ├── test_graph.py                   # Full LangGraph integration test
│   └── test_cross_reference.py
├── .env
├── requirements.txt
└── render.yaml

verif-ai-frontend/
├── AGENTS.md                           ← Frontend agent context
├── src/
│   ├── pages/
│   │   ├── Login.jsx
│   │   ├── StudentUpload.jsx
│   │   ├── AnalysisResults.jsx         # Research log panel here
│   │   └── RecruiterDashboard.jsx
│   ├── components/
│   │   ├── TrustScoreGauge.jsx         # Animated 0-100 gauge
│   │   ├── ResearchLogPanel.jsx        # Grok-style animated thoughts
│   │   ├── AgentThinkingCard.jsx       # Individual research step card
│   │   ├── FlagsList.jsx
│   │   └── DocumentUploader.jsx
│   ├── hooks/
│   │   ├── useWebSocket.js             # WebSocket connection hook
│   │   └── useFirebaseAuth.js
│   └── App.jsx
└── package.json
```

---

## ⏱️ 48-HOUR BUILD ROADMAP

### Hour 0–3: Foundation
- [ ] Create both GitHub repos
- [ ] Firebase project → enable Email + Google Auth
- [ ] MongoDB Atlas cluster → get connection string
- [ ] FastAPI skeleton + `.env` setup
- [ ] Firebase Admin SDK connection test
- [ ] MongoDB Motor connection test

### Hour 3–6: Auth + File Upload
- [ ] Firebase JWT verification middleware
- [ ] `POST /auth/sync` — sync Firebase user to Firestore
- [ ] MongoDB GridFS upload endpoint
- [ ] SHA-256 hash generation on upload
- [ ] Frontend: login page + drag-drop upload UI

### Hour 6–8: LangGraph State + Graph Structure
- [ ] Write `services/graph/state.py` — VerificationState TypedDict
- [ ] Write `graph_builder.py` — assemble StateGraph with all nodes + edges
- [ ] Test graph compiles with stub nodes (return hardcoded data)
- [ ] WebSocket endpoint that streams graph events

### Hour 8–16: The Three Agent Nodes (Core Work)
- [ ] Write all tools in `services/tools/`
- [ ] `resume_node.py` — LangChain + Gemini Flash + stylometrics
- [ ] `certificate_node.py` — Gemini Vision + ELA + OCR
- [ ] `github_node.py` — Deep Agent + PyGithub + OSINT
- [ ] Test each node independently with real data
- [ ] Save research logs to Firebase Firestore after each node

### Hour 16–18: Cross-Reference + Final Decision
- [ ] `cross_reference.py` — GitHub vs Resume cross-checks
- [ ] `final_decision.py` — weighted trust score formula
- [ ] Full graph end-to-end test with real student data

### Hour 18–22: Frontend Results UI
- [ ] `ResearchLogPanel.jsx` — animated Grok-style research steps
- [ ] Trust Score gauge (0-100, color coded)
- [ ] Per-agent score cards
- [ ] Recruiter search page

### Hour 22–28: Testing + Polish
- [ ] Seed 5 test profiles (2 clean, 2 suspicious, 1 fake)
- [ ] pytest for all nodes + full graph
- [ ] Error handling for API failures
- [ ] Loading states + offline fallback

### Hour 28–36: Deploy + Demo Prep
- [ ] Deploy backend to Render
- [ ] Deploy frontend to Vercel
- [ ] End-to-end test on deployed version
- [ ] Record 60-second backup demo video
- [ ] Prepare 3 test accounts for live demo

---

## 🛠️ COMPLETE TECH STACK

| Layer | Technology | Package | Why |
|-------|-----------|---------|-----|
| Frontend | React + Vite + Tailwind v4 | — | Fast, you know it |
| Auth | Firebase Auth | firebase (JS SDK) | Zero backend auth code |
| User Data | Firebase Firestore | firebase-admin | Real-time, structured |
| File Storage | MongoDB GridFS | motor | Binary files, 16MB+ support |
| Backend | FastAPI | fastapi | Async Python |
| **Agent Framework** | **LangGraph** | `langgraph` | **Multi-agent shared state** |
| Agent Orchestration | LangChain | `langchain` | Tools, chains, prompts |
| LLM (text) | Gemini 1.5 Flash | `langchain-google-genai` | Fast + cheap |
| LLM (vision) | Gemini 1.5 Pro | `langchain-google-genai` | Image understanding |
| MCP in Python | langchain-mcp-adapters | `langchain-mcp-adapters` | MCP tools in agents |
| Agent Tracing | LangSmith | `langsmith` | Debug every agent step |
| PDF Parsing | pdfplumber | `pdfplumber` | Best text extraction |
| OCR | pytesseract | `pytesseract` | Certificate text |
| Image Forensics | Pillow | `Pillow` | ELA analysis |
| GitHub OSINT | PyGithub | `PyGithub` | Repo + commit analysis |
| Code Complexity | radon | `radon` | Cyclomatic complexity |
| HTTP | httpx | `httpx` | Async only, never requests |
| Testing (API) | **Bruno** | — | Best Postman alternative, free |
| Testing (Python) | pytest-asyncio | `pytest-asyncio` | Async test support |
| Deploy Backend | Render.com | — | Free FastAPI hosting |
| Deploy Frontend | Vercel | — | Free React hosting |

---

## 🧪 TESTING STRATEGY — COMPLETE GUIDE

### Tool Recommendation: Bruno (Not Postman)

**Why Bruno over Postman:**
- Fully free, open-source, no account needed
- Stores collections as files in your repo — commit them with git
- Supports WebSocket testing natively
- Import from Postman if needed
- Download: https://www.usebruno.com/

**Also useful:**
- **Hoppscotch** (https://hoppscotch.io) — web-based, best for WebSocket + SSE testing, zero install
- **Thunder Client** — VSCode extension, good for quick tests without leaving editor

### What to Test and How

**Phase 1 — Auth Endpoints**
```
Test: POST /api/v1/auth/sync
Headers: Authorization: Bearer <firebase_jwt>
Body: {"firebase_uid": "abc", "email": "test@test.com", "role": "student"}
Expected: 201 {"success": true, "data": {"user_id": "..."}}

Test: GET /api/v1/auth/me
Headers: Authorization: Bearer <valid_jwt>
Expected: 200 with user object

Test: GET /api/v1/auth/me
Headers: Authorization: Bearer <expired_jwt>
Expected: 401 {"success": false, "error": "Invalid token"}
```

**Phase 2 — File Upload Endpoints**
```
Test: POST /api/v1/documents/upload
Form: file=resume.pdf, type=resume, student_id=abc123
Expected: 201 with document_id and hash_sha256

Test: POST /api/v1/documents/upload
Form: file=10mb_resume.pdf (oversized)
Expected: 400 {"error": "File too large", "max_size_mb": 10}

Test: POST /api/v1/documents/upload
Form: file=malware.exe, type=resume
Expected: 400 {"error": "Invalid file type"}
```

**Phase 3 — Analysis Trigger**
```
Test: POST /api/v1/analysis/start
Body: {
  "student_id": "abc",
  "resume_document_id": "doc_id",
  "certificate_document_ids": ["cert_id_1"],
  "github_url": "https://github.com/testuser"
}
Expected: 202 with job_id and websocket_url
```

**Phase 4 — WebSocket Research Log Stream**
```
Connect: ws://localhost:8000/api/v1/analysis/stream/{job_id}?token=<firebase_jwt>
Expected message sequence:
  1. {"type": "thinking_token", "agent": "resume", "content": "Analyzing..."}
  2. {"type": "research_step_start", "data": {...}}
  3. {"type": "research_step_complete", "data": {...}}
  4. {"type": "analysis_complete", "data": {"trust_score": 42}}

Use Hoppscotch for this — best WebSocket testing UI
```

**Phase 5 — Results Endpoints**
```
Test: GET /api/v1/analysis/result/{student_id}
Test: GET /api/v1/analysis/logs/{result_id}
Test: GET /api/v1/verification/search?email=test@test.com
```

### pytest Test Structure

```python
# tests/conftest.py — shared test fixtures
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch

@pytest.fixture
async def client():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

@pytest.fixture
def mock_firebase_token():
    """Mock Firebase JWT verification — don't make real Firebase calls in tests"""
    with patch("app.core.firebase.verify_firebase_token") as mock:
        mock.return_value = {"uid": "test_uid", "email": "test@test.com"}
        yield mock

@pytest.fixture
def mock_gemini():
    """Mock all Gemini API calls — don't burn API credits in tests"""
    with patch("langchain_google_genai.ChatGoogleGenerativeAI") as mock:
        mock.return_value.ainvoke = AsyncMock(return_value={"trust_score": 75})
        yield mock

# tests/test_resume_node.py
@pytest.mark.asyncio
async def test_resume_node_detects_ai_text(mock_gemini):
    from app.services.graph.resume_node import resume_agent_node
    state = {
        "resume_doc_id": "test_doc",
        "research_logs": [],
        "flags": []
    }
    result = await resume_agent_node(state)
    assert "resume_result" in result
    assert "overall_resume_trust" in result["resume_result"]
    assert 0 <= result["resume_result"]["overall_resume_trust"] <= 100

@pytest.mark.asyncio
async def test_full_langgraph_pipeline(mock_gemini, mock_firebase_token):
    """Test complete graph runs without errors"""
    from app.services.graph.graph_builder import app as langgraph_app
    state = {
        "student_id": "test",
        "resume_doc_id": "doc1",
        "cert_doc_ids": ["cert1"],
        "github_url": "https://github.com/testuser",
        "research_logs": [],
        "flags": [],
        "completed_agents": []
    }
    result = await langgraph_app.ainvoke(state)
    assert result["overall_trust_score"] is not None
    assert result["verdict"] in ["AUTHENTIC", "FLAGGED", "SUSPICIOUS", "FAKE"]
```

---

## 📊 RESEARCH LOG — GROK-STYLE JSON (Complete Schema)

```json
{
  "log_id": "firebase_doc_id",
  "result_id": "firebase_doc_id",
  "student_uid": "firebase_uid",
  "agent_type": "resume | certificate | github | supervisor",
  "status": "running | complete | failed",
  "created_at": "ISO8601",
  "logs": [
    {
      "step": 1,
      "type": "thinking | tool_start | tool_end | cross_reference | decision",
      "agent": "resume_agent | cert_agent | github_agent | supervisor",
      "thought": "I need to verify if TechCorp Solutions actually existed in 2017...",
      "action": "web_search",
      "query": "TechCorp Solutions Bangalore India founded year",
      "sources": [
        "https://www.linkedin.com/company/techcorp-solutions",
        "https://techcorp.in/about-us"
      ],
      "finding": "Company incorporated in 2019 per MCA records. Candidate claims 2017 employment. Chronologically impossible.",
      "impact": "HIGH_FLAG",
      "flag_generated": {
        "type": "timeline_impossibility",
        "detail": "TechCorp Solutions founded 2019, candidate claims employment from 2017",
        "severity": "high",
        "evidence_url": "https://linkedin.com/company/techcorp-solutions"
      },
      "cross_agent_reference": null,
      "timestamp": "2025-01-01T10:00:01.000Z",
      "duration_ms": 1240
    },
    {
      "step": 5,
      "type": "cross_reference",
      "agent": "supervisor",
      "thought": "Resume claims 3yr React experience. Let me check GitHub evidence from github_agent findings.",
      "action": "read_state",
      "finding": "GitHub agent found 0 React repos. Resume claims 3yr React experience. MISMATCH.",
      "impact": "HIGH_FLAG",
      "cross_agent_reference": {
        "from_agent": "github_agent",
        "referenced_field": "github_result.languages_used",
        "value_found": ["Python", "Java"],
        "expected": "React should be present"
      },
      "timestamp": "2025-01-01T10:00:08.000Z",
      "duration_ms": 45
    }
  ],
  "summary_stats": {
    "total_steps": 12,
    "web_searches": 6,
    "cross_agent_checks": 3,
    "high_flags": 3,
    "medium_flags": 1,
    "low_flags": 0,
    "sources_visited": ["linkedin.com", "github.com", "mca.gov.in"],
    "total_duration_ms": 18400,
    "agents_involved": ["resume_agent", "github_agent", "supervisor"]
  }
}
```

---

## 🏆 WHY THIS WINS

### 1. LangGraph Architecture — Technically Impressive
Using LangGraph StateGraph shows judges you understand production AI architecture, not just "call an LLM." Shared state + cross-agent reasoning is how real enterprise AI systems are built.

### 2. Research Log Transparency — The Killer Feature
Every research step, every source visited, every cross-agent reference — live streamed in real time. Judges see AI reasoning, not just a score.

### 3. Cross-Agent Reasoning — Nobody Else Has This
GitHub agent's findings feed into Resume agent's evaluation. Certificates are checked against GitHub evidence. This is multi-dimensional verification that humans can't do at scale.

### 4. Correct Technology Choices
Firebase for auth (battle-tested), MongoDB for files (efficient), LangGraph for agents (cutting-edge), Gemini for LLM (Google hackathon). Every choice has a reason.

### 5. Three-Dimensional Verification
Resume + Certificates + Code portfolio together. No existing tool does all three with AI reasoning.

---

## 📚 COMPLETE RESOURCE LIST

### LangGraph (Core)
- **LangGraph Docs:** https://langchain-ai.github.io/langgraph/
- **StateGraph How-To:** https://langchain-ai.github.io/langgraph/how-tos/create-react-agent/
- **LangGraph Multi-Agent:** https://langchain-ai.github.io/langgraph/concepts/multi_agent/
- **LangGraph Streaming:** https://langchain-ai.github.io/langgraph/how-tos/streaming/
- **LangGraph GitHub:** https://github.com/langchain-ai/langgraph
- **Deep Agents with LangGraph (Free Course):** https://academy.langchain.com/courses/deep-agents-with-langgraph

### LangChain + Gemini
- **LangChain Docs:** https://docs.langchain.com/oss/python/langchain/overview
- **ChatGoogleGenerativeAI:** https://docs.langchain.com/oss/python/integrations/chat/google_generative_ai
- **LangChain MCP Adapters:** https://github.com/langchain-ai/langchain-mcp-adapters
- **LangChain MCP Docs:** https://docs.langchain.com/oss/python/langchain/mcp
- **Deep Agents SDK:** https://docs.langchain.com/oss/python/deepagents/overview
- **Structured Output:** https://docs.langchain.com/oss/python/langchain/structured-output
- **astream_events Guide:** https://docs.langchain.com/oss/python/langchain/event-streaming
- **LangChain Academy (Foundation):** https://academy.langchain.com/courses/foundation-introduction-to-langchain-python
- **All LangChain Providers:** https://docs.langchain.com/oss/python/integrations/providers/overview
- **LangChain Google Provider:** https://docs.langchain.com/oss/python/integrations/providers/google
- **LangChain Reference:** https://docs.langchain.com/oss/python/reference/overview

### LangSmith (Observability)
- **LangSmith Dashboard:** https://smith.langchain.com
- **Tracing Guide:** https://docs.smith.langchain.com/observability/tutorials/tracing

### Google AI
- **Gemini API Docs:** https://ai.google.dev/gemini-api/docs
- **Google AI Studio:** https://aistudio.google.com
- **Gemini Structured Output:** https://ai.google.dev/gemini-api/docs/structured-output
- **Gemini Vision Guide:** https://ai.google.dev/gemini-api/docs/vision

### Firebase
- **Firebase Admin SDK:** https://firebase.google.com/docs/admin/setup
- **Firebase Auth + FastAPI:** https://firebase.google.com/docs/admin/verify-id-tokens
- **Firestore Python Client:** https://firebase.google.com/docs/firestore/quickstart
- **Firebase JS SDK (Frontend):** https://firebase.google.com/docs/auth/web/start

### MongoDB (Files Only)
- **Motor Async Driver:** https://motor.readthedocs.io/
- **GridFS with Motor:** https://motor.readthedocs.io/en/stable/api-motor/motor_gridfs.html
- **MongoDB Atlas Free Tier:** https://www.mongodb.com/cloud/atlas

### Testing Tools
- **Bruno (Best Postman alt):** https://www.usebruno.com/
- **Hoppscotch (WebSocket testing):** https://hoppscotch.io
- **FastAPI TestClient Docs:** https://fastapi.tiangolo.com/tutorial/testing/
- **pytest-asyncio:** https://pytest-asyncio.readthedocs.io/

### PDF + Image Forensics
- **pdfplumber:** https://github.com/jsvine/pdfplumber
- **pypdf (metadata):** https://github.com/py-pdf/pypdf
- **pytesseract:** https://github.com/madmaze/pytesseract
- **Pillow (ELA):** https://pillow.readthedocs.io/

### GitHub OSINT
- **PyGithub:** https://pygithub.readthedocs.io/
- **GitHub REST API:** https://docs.github.com/en/rest
- **radon (complexity):** https://radon.readthedocs.io/

### Architecture + Pitch
- **Architecture Diagrams:** https://app.eraser.io
- **Wireframes:** https://excalidraw.com
- **Pitch Deck:** https://gamma.app
- **Render Deploy Guide:** https://render.com/docs/deploy-fastapi
- **Vercel + Vite:** https://vercel.com/docs/frameworks/vite

---

## ⚠️ CRITICAL THINGS TO AVOID

1. **Don't skip LangGraph shared state** — it's the architecture that makes cross-agent reasoning possible
2. **Don't run agents sequentially** — always parallel via LangGraph's parallel branch support
3. **Don't put files in Firebase** — MongoDB GridFS only for PDFs and images
4. **Don't put auth in MongoDB** — Firebase Auth + Firestore for everything user-related
5. **Don't use raw google-generativeai** — always via `langchain-google-genai`
6. **Don't skip research logs** — this is your winning differentiator
7. **Don't demo on live internet** — prepare cached responses as fallback
8. **Don't build blockchain** — save it for future roadmap pitch
9. **Don't use Postman** — Bruno is free, better, and stores collections in git

---

## 🎤 PITCH SCRIPT (90 seconds)

> "Imagine you're a recruiter at a fast-growing startup. You have 200 applications in your inbox. Research shows that over 45% of them used AI tools to write their resumes. Some certificates are photoshopped. Some GitHub portfolios are staged.
>
> You have no way to know without spending days on manual verification.
>
> VERIF-AI solves this in 60 seconds.
>
> A student submits their resume, certificates, and GitHub URL. Our three AI agents — built on LangGraph and powered by Google Gemini — analyze each simultaneously. But here's what's different: the agents talk to each other. The GitHub agent tells the Resume agent 'There are zero React commits here.' The Resume agent finds that suspicious. The Supervisor cross-references everything.
>
> And you — the recruiter — see every single step. Every website the AI visited. Every contradiction it found. Every conclusion it reached. Live, in real time.
>
> The result is a Trust Score from 0 to 100 with a complete, transparent reasoning trail.
>
> Faster verification. Fairer hiring. Full transparency.
>
> This is VERIF-AI."

---

## 🔮 FUTURE ROADMAP

- **Blockchain anchoring** — Polygon for tamper-proof verification records
- **ZK-Proof privacy** — Prove credentials without revealing personal data
- **Institution API** — Direct university integration for certificate source verification
- **Browser extension** — One-click LinkedIn profile verification for recruiters
- **Mobile app** — Scan physical certificates with phone camera
- **Fine-tuned Gemma 4** — Custom fraud detection model on academic dataset

---

*Built with LangGraph. Powered by Gemini. Verified by three AI agents that talk to each other.*
