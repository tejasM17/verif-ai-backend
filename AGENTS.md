# VERIF-AI Backend — OpenCode Agent Rules
> File: `verif-ai-backend/AGENTS.md`
> OpenCode reads this automatically. Run `/init` if context is lost.

---

## 🔴 AUTO-UPDATE RULE

After every completed task:
1. Mark `[x]` in STATUS TRACKER below
2. Update `contracts/CONTRACT.md`
3. `@git commit -m "feat: [name]" && git push`

---

## PROJECT OVERVIEW

VERIF-AI — AI-powered credential verification. Three LangGraph agents analyze resume + certificates + GitHub in parallel, communicate via shared state, cross-reference findings, then produce a Trust Score (0-100) with Grok-style live research logs.

**This repo:** FastAPI backend only.
**Partner repo:** `verif-ai-frontend` (NEVER TOUCH).
**Shared truth:** `contracts/CONTRACT.md` — update after every API change.

---

## HOW STUDENT ↔ RECRUITER WORKS

```
STUDENT:
  Register (role=student) → Upload docs → Trigger analysis →
  Get Trust Score → Toggle profile_public=true →
  Profile appears in recruiter search index →
  Share personal link: /profile/{uid}

RECRUITER:
  Register (role=recruiter) → Go to Discover page →
  Search by: skills, trust_score_min, domain, location →
  View student public profile + full research log →
  Shortlist students → Export shortlist

LINK:
  Student shares: https://verif-ai.app/profile/{firebase_uid}
  This URL is public if profile_public=true
  Trust Score visible to all recruiters
  Research logs visible to all recruiters (transparency feature)
```

---

## TECH STACK

```
FastAPI (Python 3.11+, always async def)
├── AI: LangGraph (StateGraph) + LangChain + Gemini
│   ├── langgraph          → multi-agent orchestration + shared state
│   ├── langchain          → tools, prompts, chains
│   ├── langchain-google-genai → Gemini 1.5 Flash + Pro
│   ├── langchain-mcp-adapters → MCP tools inside Python agents
│   └── langsmith          → trace every agent step
├── Database split:
│   ├── Firebase Firestore  → users, results, profiles, shortlists (ALL structured data)
│   └── MongoDB GridFS      → resume PDFs + certificate images ONLY
├── Auth: Firebase Admin SDK (JWT verify)
├── PDF: pdfplumber + pypdf
├── OCR + Forensics: pytesseract + Pillow (ELA)
├── GitHub: PyGithub + radon
└── HTTP: httpx (NEVER requests)
```

---

## PROJECT STRUCTURE

```
verif-ai-backend/
├── AGENTS.md                    ← This file (update STATUS TRACKER)
├── app/
│   ├── api/v1/
│   │   ├── auth.py              # Firebase JWT + user sync
│   │   ├── documents.py         # MongoDB GridFS upload
│   │   ├── analysis.py          # LangGraph trigger + WebSocket
│   │   ├── profile.py           # Student: publish/unpublish profile
│   │   ├── discover.py          # Recruiter: browse + search
│   │   └── verification.py      # Results + shortlist
│   ├── services/
│   │   ├── graph/
│   │   │   ├── state.py         # VerificationState TypedDict
│   │   │   ├── supervisor.py
│   │   │   ├── resume_node.py   # Agent 1
│   │   │   ├── certificate_node.py # Agent 2
│   │   │   ├── github_node.py   # Agent 3
│   │   │   ├── cross_reference.py
│   │   │   ├── final_decision.py
│   │   │   └── graph_builder.py # compile graph here
│   │   ├── tools/
│   │   │   ├── pdf_tools.py
│   │   │   ├── image_tools.py   # ELA mandatory
│   │   │   ├── github_tools.py
│   │   │   └── stylometry_tools.py
│   │   ├── streaming.py         # astream_events v3 → WebSocket
│   │   ├── trust_score.py
│   │   └── discovery_service.py # Firestore search queries
│   ├── models/
│   │   ├── user.py              # Beanie (MongoDB)
│   │   └── document.py          # Beanie (MongoDB GridFS metadata)
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── document.py
│   │   ├── analysis.py
│   │   ├── profile.py
│   │   └── discover.py
│   ├── core/
│   │   ├── database.py          # Motor + GridFS
│   │   ├── firebase.py          # Admin + Firestore + JWT deps
│   │   ├── config.py            # Pydantic BaseSettings
│   │   └── langchain_setup.py   # LLM factory + LangSmith
│   └── main.py
├── contracts/CONTRACT.md        ← UPDATE AFTER EVERY API CHANGE
├── tests/
└── render.yaml
```

---

## LANGGRAPH PATTERNS — ALWAYS USE

### State
```python
from typing import TypedDict, Optional, Annotated
import operator

class VerificationState(TypedDict):
    student_uid: str
    resume_doc_id: str
    cert_doc_ids: list[str]
    github_url: str
    resume_result: Optional[dict]
    cert_result: Optional[dict]
    github_result: Optional[dict]
    cross_ref_findings: Optional[list]
    research_logs: Annotated[list[dict], operator.add]  # append-only
    flags: Annotated[list[dict], operator.add]          # append-only
    completed_agents: Annotated[list[str], operator.add]
    overall_trust_score: Optional[float]
    verdict: Optional[str]
```

### Graph Build
```python
from langgraph.graph import StateGraph, END

workflow = StateGraph(VerificationState)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("resume_agent", resume_agent_node)
workflow.add_node("cert_agent", certificate_agent_node)
workflow.add_node("github_agent", github_agent_node)
workflow.add_node("cross_reference", cross_reference_node)
workflow.add_node("final_decision", final_decision_node)
workflow.set_entry_point("supervisor")
# Parallel dispatch
workflow.add_edge("supervisor", "resume_agent")
workflow.add_edge("supervisor", "cert_agent")
workflow.add_edge("supervisor", "github_agent")
# Conditional: wait for all 3, then cross-reference
workflow.add_conditional_edges("resume_agent", all_done_router, ...)
workflow.add_edge("cross_reference", "final_decision")
workflow.add_edge("final_decision", END)
app = workflow.compile()
```

### LLM Setup
```python
from langchain_google_genai import ChatGoogleGenerativeAI

llm_flash = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.1, streaming=True
)
llm_vision = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.1, streaming=True
)
# ALWAYS use structured output
structured = llm_flash.with_structured_output(
    schema=AgentResult.model_json_schema(),
    method="json_schema"
)
```

### Streaming
```python
async for event in agent.astream_events(input, version="v3"):
    if event["event"] == "on_chat_model_stream":
        yield {"type": "thinking_token", "content": event["data"]["chunk"].content}
    elif event["event"] == "on_tool_start":
        yield {"type": "research_step_start", "data": build_step(event)}
    elif event["event"] == "on_tool_end":
        yield {"type": "research_step_complete", "data": update_step(event)}
    elif event["event"] == "on_chain_end" and event.get("name") == "agent":
        yield {"type": "analysis_complete", "data": final_result}
```

---

## THE AGENTS

### Agent 1 — Resume Node
- PDF → pdfplumber → extract text
- Local: burstiness, type-token ratio, avg sentence length (NO API)
- LangChain agent: Gemini Flash + web_search tool
- Reads from state to cross-check GitHub findings if available
- Output schema (Pydantic):
  ```
  ai_text_probability, skill_inflation_score, timeline_consistency,
  overall_resume_trust, flags[], research_steps[], summary
  ```

### Agent 2 — Certificate Node
- Each file: detect mime → route PDF or image pipeline
- Image: pytesseract OCR + PIL ELA (MANDATORY — never skip ELA)
- PDF: pypdf metadata + pdfplumber text
- Gemini Vision: image bytes + OCR text + metadata
- Output: `forgery_probability, issuer_verified, visual_tampering_score, overall_cert_trust, flags[], research_steps[], summary`

### Agent 3 — GitHub Node
- PyGithub: profile, all repos, commits from top 10 repos
- Compute: fork_ratio, burst_score, commit_msg_quality, readme_only_count
- Extract code from top 5 repos → radon complexity
- LangChain Deep Agent: web search + GitHub data + cross-check resume skills from state
- Output: `originality_score, skill_match_score, commit_authenticity, overall_github_trust, flags[], research_steps[], summary`

### Cross-Reference Node
- Runs AFTER all 3 agents complete
- Checks: resume skills vs GitHub languages
- Checks: resume employment dates vs GitHub first commits
- Checks: certificate courses vs GitHub project evidence
- Appends cross_ref_findings to state

### Final Decision Node
- `trust_score = resume×0.40 + cert×0.35 + github×0.25`
- Verdict: AUTHENTIC(≥80) | FLAGGED(60-79) | SUSPICIOUS(35-59) | FAKE(<35)
- Save to Firestore: /verifications/{id}
- Update Firestore /profiles/{uid} with new trust_score

---

## DISCOVERY SERVICE

```python
# services/discovery_service.py
from firebase_admin import firestore

async def search_public_profiles(
    skills: list[str] = None,
    min_trust: float = 0,
    domain: str = None,
    limit: int = 20
) -> list[dict]:
    """Query Firestore profiles collection for public verified students"""
    db = firestore.client()
    query = db.collection("profiles").where("is_public", "==", True)
    if min_trust > 0:
        query = query.where("trust_score", ">=", min_trust)
    if domain:
        query = query.where("domain", "==", domain)
    query = query.order_by("trust_score", direction=firestore.Query.DESCENDING)
    query = query.limit(limit)
    docs = query.stream()
    return [doc.to_dict() for doc in docs]
```

---

## RESEARCH LOG SCHEMA

```json
{
  "log_id": "firestore_doc_id",
  "result_id": "ai_results doc id",
  "student_uid": "firebase_uid",
  "agent_type": "resume|certificate|github|supervisor",
  "status": "running|complete|failed",
  "logs": [
    {
      "step": 1,
      "type": "tool_start",
      "agent": "resume_agent",
      "thought": "Checking if TechCorp existed before 2017...",
      "action": "web_search",
      "query": "TechCorp Solutions Bangalore founded year",
      "sources": ["https://linkedin.com/company/techcorp"],
      "finding": "Founded 2019. Employment claim of 2017 impossible.",
      "impact": "HIGH_FLAG",
      "flag_generated": {
        "type": "timeline_impossibility",
        "detail": "Company founded 2019, candidate claims 2017",
        "severity": "high"
      },
      "cross_agent_reference": null,
      "timestamp": "ISO8601",
      "duration_ms": 1240
    }
  ],
  "summary_stats": {
    "total_steps": 8,
    "high_flags": 2,
    "sources_visited": ["linkedin.com", "github.com"],
    "total_duration_ms": 14000
  }
}
```

---

## CODING STANDARDS

1. All `async def` + `await` on all I/O
2. All LLM via `langchain-google-genai`
3. Structured output: `with_structured_output(schema, method="json_schema")`
4. Streaming: `astream_events(version="v3")`
5. `return_exceptions=True` in any asyncio.gather
6. Never skip `research_steps` in agent output
7. Never use `requests` — `httpx` only
8. Always try/except Gemini + GitHub + Firestore calls
9. Update CONTRACT.md after every endpoint change

---

## MODEL SELECTION (OpenCode)

| Task | Use Model |
|------|----------|
| Complex agent logic | `deepseek-r1:14b` |
| Writing LangChain/LangGraph code | `deepseek-coder-v2:16b` |
| MongoDB queries, schemas | `qwen2.5-coder:14b` |
| Debugging | `deepseek-r1:14b` |
| Long context review | `minimax-text-01` |

---

## ENV VARS

```
MONGODB_URI, MONGODB_DB_NAME=verifai
FIREBASE_PROJECT_ID, FIREBASE_CREDENTIALS_JSON
GEMINI_API_KEY, GOOGLE_API_KEY (same)
LANGCHAIN_TRACING_V2=true, LANGCHAIN_API_KEY, LANGCHAIN_PROJECT=verif-ai-hackathon
GITHUB_TOKEN, BRAVE_API_KEY
ALLOWED_ORIGINS, PORT=8000, ENVIRONMENT
```

---

## MCP TOOLS

```
@mongodb   → seed data, query, schemas
@github    → push, branch, PR
@render    → deploy
@git       → commit after every feature
```

---

## STATUS TRACKER

**Phase 0: Foundation**
- [ ] requirements.txt
- [ ] .env + .gitignore
- [ ] core/config.py
- [ ] core/database.py
- [ ] core/firebase.py
- [ ] core/langchain_setup.py
- [ ] main.py

**Phase 1: Auth**
- [ ] models/user.py
- [ ] schemas/auth.py
- [ ] api/v1/auth.py

**Phase 2: Upload**
- [ ] models/document.py
- [ ] schemas/document.py
- [ ] api/v1/documents.py

**Phase 3: Agents**
- [ ] services/graph/state.py
- [ ] services/tools/ (all 4 files)
- [ ] services/graph/supervisor.py
- [ ] services/graph/resume_node.py
- [ ] services/graph/certificate_node.py
- [ ] services/graph/github_node.py
- [ ] services/graph/cross_reference.py
- [ ] services/graph/final_decision.py
- [ ] services/graph/graph_builder.py
- [ ] services/streaming.py
- [ ] services/trust_score.py
- [ ] api/v1/analysis.py

**Phase 4: Discovery**
- [ ] services/discovery_service.py
- [ ] schemas/profile.py + discover.py
- [ ] api/v1/profile.py
- [ ] api/v1/discover.py
- [ ] api/v1/verification.py

**Phase 5: Tests + Deploy**
- [ ] tests/ (all test files)
- [ ] Seed 5 profiles @mongodb
- [ ] render.yaml + deploy

**CONTRACT.md last updated:** _not yet_
