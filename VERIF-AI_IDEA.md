# VERIF-AI — Master Idea Document (Updated)
### AI-Powered Academic Profile & Skill Verification System
#### LangGraph Multi-Agent + Google Gemini + Firebase + MongoDB

---

## 🎯 ONE-LINE PITCH

> **"VERIF-AI is a LangGraph-powered multi-agent system where three specialized AI agents collaborate, share findings, and collectively decide whether a student's resume, certificates, and GitHub are genuine — giving recruiters a transparent Trust Score with full live AI reasoning."**

---

## 🔴 THE PROBLEM

| Fraud Type | Scale |
|-----------|-------|
| AI-generated resumes | 45%+ of 2025 applicants use AI tools |
| Forged certificates | PDF editing takes 10 min, detection takes 3 days |
| Ghost GitHub portfolios | Repos cloned/staged before applications |
| Manual verification | 7 seconds per resume, fraud easily passes |

No tool today verifies all three simultaneously with explainable reasoning.

---

## 🟢 WHAT YOU'RE BUILDING

```
Student uploads → 3 LangGraph agents run in parallel →
Agents share state + cross-reference → Trust Score (0-100) →
Student publishes profile → Recruiter discovers + searches → Hires
```

---

## 👤 USER FLOWS (COMPLETE)

### Student Flow
```
1. Register (role=student) → Firebase Auth
2. Upload resume PDF + certificate images + GitHub URL → MongoDB GridFS
3. Click "Analyze My Profile" → LangGraph pipeline runs
4. Watch live: animated research log (Grok-style thoughts + sources)
5. Receive Trust Score + verdict (AUTHENTIC/FLAGGED/SUSPICIOUS/FAKE)
6. Toggle "Make Profile Public" → appears in recruiter search
7. Share personal link: verif-ai.app/profile/{uid}
```

### Recruiter Flow
```
1. Register (role=recruiter) → Firebase Auth
2. Go to "Discover Talent" tab
3. Search: filter by skills, minimum Trust Score, domain, location
4. Browse ranked list of verified public student profiles
5. Click any student → see full Trust Score + research log panel
6. Shortlist students → build hiring pipeline
```

### How They Connect — Three Ways
```
Way 1: Student shares direct link → recruiter views public profile
Way 2: Recruiter searches "Python + min_trust=70" → student appears in results
Way 3: Recruiter browses all public profiles sorted by Trust Score
```

---

## 🏗️ SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────────────┐
│  STUDENT PORTAL          RECRUITER PORTAL               │
│  Upload docs             Discover + Search               │
└──────────────┬───────────────────────┬──────────────────┘
               │ FastAPI + Firebase JWT │
               ▼                       ▼
┌─────────────────────────────────────────────────────────┐
│              LANGGRAPH SUPERVISOR NODE                  │
│  Creates VerificationState → dispatches all 3 agents    │
└──────┬──────────────────┬──────────────────┬────────────┘
       │ parallel         │ parallel         │ parallel
       ▼                  ▼                  ▼
┌────────────┐  ┌──────────────────┐  ┌──────────────┐
│ RESUME     │  │ CERTIFICATE      │  │ GITHUB       │
│ AGENT      │  │ AGENT            │  │ AGENT        │
│            │  │                  │  │              │
│ Gemini     │  │ Gemini Vision    │  │ Deep Agent   │
│ Flash      │  │ Pro              │  │ Gemini Flash │
│            │  │                  │  │              │
│ Tools:     │  │ Tools:           │  │ Tools:       │
│ PDF parse  │  │ OCR + ELA        │  │ GitHub API   │
│ Stylometry │  │ PDF metadata     │  │ Commit OSINT │
│ Web search │  │ Web search       │  │ Code quality │
│            │  │                  │  │ Web search   │
│ → State    │  │ → State          │  │ → State      │
└────────────┘  └──────────────────┘  └──────────────┘
       │                  │                  │
       └──────────────────┴──────────────────┘
                          │ All 3 complete
                          ▼
           ┌──────────────────────────────┐
           │ CROSS-REFERENCE NODE         │
           │ GitHub langs vs Resume skills│
           │ Commit dates vs Resume dates │
           │ Certs vs GitHub evidence     │
           └──────────────┬───────────────┘
                          ▼
           ┌──────────────────────────────┐
           │ FINAL DECISION NODE          │
           │ trust = r×0.40+c×0.35+g×0.25│
           │ Save to Firebase Firestore   │
           └──────────────────────────────┘
```

---

## 🗄️ DATA ARCHITECTURE — STRICT SPLIT

### Firebase = Everything except files
```
Firebase Auth    → login, JWT tokens, user sessions
Firestore:
  /users/{uid}           → email, role, display_name
  /verifications/{id}    → trust_score, verdict, all agent scores
  /ai_results/{id}       → per-agent scores and flags
  /research_logs/{id}    → full step-by-step AI reasoning trail
  /profiles/{uid}        → is_public, skills, domain, trust_score (for search)
  /shortlists/{uid}      → recruiter's shortlisted student UIDs
```

### MongoDB = Files ONLY
```
GridFS:
  resumes bucket      → resume PDF bytes
  certificates bucket → certificate image/PDF bytes

documents collection:
  firebase_uid, type, gridfs_id, filename, hash_sha256, status
```

**Why this split:** Firebase is better for structured real-time data. MongoDB GridFS is better for large binary files. Firebase Auth is battle-tested. This is the cleanest architecture.

---

## 🧠 LANGGRAPH — WHY IT'S THE RIGHT CHOICE

```
Simple chatbot → LangChain is enough
Multi-agent with shared findings → LangGraph is required
```

LangGraph gives VERIF-AI three things nothing else can:
1. **Shared State** — GitHub agent's findings are visible to Resume agent's evaluation
2. **Conditional Edges** — cross-reference only runs AFTER all 3 agents complete
3. **State Accumulation** — `research_logs` append across all agents without overwriting

The cross-reference node is ONLY possible because of LangGraph shared state. It checks things like: "Resume claims 3yr React experience. GitHub agent found zero React repos. That's a HIGH FLAG." No other architecture lets agents communicate this way.

---

## 🤖 THE THREE AGENTS

### Agent 1 — Resume Analyzer
**Key science:** AI text has low "burstiness" (uniform complexity). Human writing varies naturally.
```
burstiness = stdev(sentence_lengths) / mean(sentence_lengths)
Human avg: 0.85+ | AI avg: 0.23 or lower — detectable WITHOUT any API
```
**What it does:** PDF extraction → local stylometrics → Gemini web search → verify companies, skills, timeline
**Output:** `ai_text_probability, skill_inflation_score, timeline_consistency, overall_resume_trust, flags[], research_steps[]`

### Agent 2 — Certificate Verifier
**Key science:** Error Level Analysis (ELA) — re-compress image at Q95, diff it, high std dev = editing
**What it does:** OCR → ELA analysis → PDF metadata → Gemini Vision → verify issuer via web search
**Output:** `forgery_probability, issuer_verified, visual_tampering_score, overall_cert_trust, flags[], research_steps[]`

### Agent 3 — GitHub Code Verifier
**Key signals:**
- Fork ratio (>80% forks = suspicious)
- Burst score (low = cramming before application)
- Commit message quality (real devs write "fix race condition", fakers write "update")
**What it does:** PyGithub OSINT → commit analysis → code samples → Gemini with web search → cross-check resume skills
**Output:** `originality_score, skill_match_score, commit_authenticity, overall_github_trust, flags[], research_steps[]`

### Cross-Reference Node (LangGraph advantage)
Runs after all 3 agents, reads all their state. Checks:
- Resume skills vs GitHub languages used
- Resume employment start dates vs GitHub first commits in that language
- Certificate courses vs GitHub project evidence

---

## 📊 RESEARCH LOG — GROK-STYLE (The Winning Feature)

```json
{
  "logs": [
    {
      "step": 1,
      "agent": "resume_agent",
      "thought": "Checking if TechCorp Solutions existed before 2017",
      "action": "web_search",
      "query": "TechCorp Solutions Bangalore India founded",
      "sources": ["https://linkedin.com/company/techcorp"],
      "finding": "Company founded 2019. Claim of 2017 impossible.",
      "impact": "HIGH_FLAG",
      "duration_ms": 1240
    },
    {
      "step": 8,
      "agent": "supervisor",
      "type": "cross_reference",
      "thought": "Resume claims 3yr React. GitHub agent found zero React repos.",
      "finding": "Skill-GitHub mismatch on React",
      "impact": "HIGH_FLAG",
      "cross_agent_reference": {
        "from_agent": "github_agent",
        "field": "languages_used",
        "value": ["Python", "Java"]
      }
    }
  ]
}
```

This streams LIVE to the frontend via WebSocket. The recruiter sees animated "thinking" cards with every step — like Grok/Perplexity's research mode.

---

## ⏱️ 48-HOUR BUILD ROADMAP

| Hours | Phase | What |
|-------|-------|------|
| 0-3 | Foundation | scaffold, core/, main.py |
| 3-6 | Auth + Upload | Firebase JWT + GridFS |
| 6-8 | LangGraph State + Graph | state.py + graph_builder.py |
| 8-16 | Three Agent Nodes | resume + cert + github nodes |
| 16-18 | Cross-ref + Final | aggregation + Firestore save |
| 18-22 | Analysis API | trigger endpoint + WebSocket |
| 22-26 | Discovery System | publish/search/shortlist |
| 26-32 | Frontend Results UI | research log panel + score gauge |
| 32-36 | Testing | pytest all phases |
| 36-40 | Deploy | Render + Vercel |
| 40-48 | Demo prep | backup video + test accounts |

---

## 🛠️ COMPLETE TECH STACK

| Layer | Tech | Why |
|-------|------|-----|
| Frontend | React + Vite + Tailwind v4 | Fast, you know it |
| Auth | Firebase Auth | Battle-tested, zero backend auth code |
| User Data | Firebase Firestore | Real-time, structured |
| File Storage | MongoDB GridFS | Binary files, 16MB+ support |
| Backend | FastAPI | Async Python, you know it |
| Agent Framework | **LangGraph** | Multi-agent shared state |
| Orchestration | LangChain | Tools, prompts, chains |
| LLM Text | Gemini 1.5 Flash | Fast, cheap |
| LLM Vision | Gemini 1.5 Pro | Certificate image understanding |
| MCP in Python | langchain-mcp-adapters | MCP tools inside agents |
| Agent Tracing | LangSmith | Debug every step |
| PDF | pdfplumber + pypdf | Text + metadata |
| OCR | pytesseract | Certificate text |
| Image Forensics | Pillow (ELA) | Forgery detection |
| GitHub OSINT | PyGithub + radon | Commits + code complexity |
| API Testing | Bruno + Hoppscotch | Free, git-friendly |
| Deploy Backend | Render.com | Free Python hosting |
| Deploy Frontend | Vercel | Free React hosting |

---

## 🏆 WHY THIS WINS

1. **LangGraph Architecture** — judges see production-grade agent design, not "call one LLM"
2. **Research Log Transparency** — live streamed AI reasoning, like Grok. Unique feature.
3. **Cross-Agent Reasoning** — GitHub findings feed Resume evaluation. Only possible with LangGraph.
4. **Complete Student→Recruiter Flow** — not just analysis, but a full platform with discovery
5. **Correct Tech Split** — Firebase for data, MongoDB for files, LangGraph for agents, Gemini for LLM

---

## ❓ JUDGE QUESTIONS + ANSWERS

**"How does a recruiter find students?"**
Three ways: search by skills/trust score, browse public profile feed, or student shares a direct link.

**"Can students game the system with someone else's GitHub?"**
Yes, and that's fine — it means they actually have the skills. We detect misrepresentation: claiming skills they don't demonstrate anywhere.

**"What about privacy?"**
Profile publishing is opt-in. Default is private. Students toggle is_public when ready. They control their own visibility always.

**"Why LangGraph instead of just calling Gemini three times?"**
LangGraph shared state lets agents talk to each other. The cross-reference node is only possible because GitHub findings are visible when evaluating the Resume. Independent API calls can't do that.

**"How accurate is it?"**
Every flag has evidence — URL, finding, reasoning. Recruiters see the AI's logic and decide. We reduce verification from 3 days to 60 seconds. We don't replace judgment, we inform it faster.

---

## 📚 ALL RESOURCES

### LangGraph
- https://langchain-ai.github.io/langgraph/
- https://langchain-ai.github.io/langgraph/concepts/multi_agent/
- https://langchain-ai.github.io/langgraph/how-tos/streaming/
- https://academy.langchain.com/courses/deep-agents-with-langgraph (free)

### LangChain + Gemini
- https://docs.langchain.com/oss/python/langchain/overview
- https://docs.langchain.com/oss/python/integrations/chat/google_generative_ai
- https://github.com/langchain-ai/langchain-mcp-adapters
- https://docs.langchain.com/oss/python/deepagents/overview
- https://academy.langchain.com/courses/foundation-introduction-to-langchain-python (free)
- https://smith.langchain.com (LangSmith tracing)

### Google AI
- https://ai.google.dev/gemini-api/docs
- https://aistudio.google.com

### Firebase
- https://firebase.google.com/docs/admin/setup
- https://firebase.google.com/docs/firestore/quickstart

### MongoDB (Files)
- https://motor.readthedocs.io/
- https://motor.readthedocs.io/en/stable/api-motor/motor_gridfs.html

### Testing
- https://www.usebruno.com/ (Bruno — best Postman alternative)
- https://hoppscotch.io (WebSocket testing)
- https://pytest-asyncio.readthedocs.io/

### Deployment
- https://render.com/docs/deploy-fastapi
- https://vercel.com/docs/frameworks/vite

---

## 🔮 FUTURE ROADMAP (Say in pitch)

- Blockchain anchoring (Polygon) for tamper-proof verification records
- ZK-Proof privacy — prove credentials without revealing personal data
- Institution API integration — verify certificates at source
- Browser extension — one-click LinkedIn verification
- Mobile app — scan physical certificates

---

*Three agents. One shared brain. Full transparency. This is VERIF-AI.*
