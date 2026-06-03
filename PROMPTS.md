# VERIF-AI — Master Prompt Engineering Guide
### Phase-by-Phase AI Agent Prompts (Gemini CLI + OpenCode)
> Use these prompts VERBATIM in your AI agents. Replace [BRACKETED] values with your actual values.

---

## HOW TO USE THIS FILE

- **Gemini CLI prompts** → paste into Gemini CLI terminal session
- **OpenCode prompts** → paste into OpenCode chat
- Each prompt is **self-contained** — it tells the agent exactly what to read, build, and where to put it
- After each prompt, wait for agent to finish, verify the file exists, then move to next

---

## ⚙️ PRE-FLIGHT: BEFORE ANY CODING

Run this ONCE at the very start to give agent full project context:

```
GEMINI CLI — Session Start Prompt:
────────────────────────────────────
Read GEMINI.md in full. Confirm you understand:
1. The complete tech stack
2. The student→recruiter flow (how they connect)
3. The LangGraph agent architecture
4. Firebase for data, MongoDB for files only
5. The auto-update rules for this file and CONTRACT.md

Reply with: "Ready. [list the 5 items confirmed]"
Do not write any code yet.
```

---

## PHASE 0: FOUNDATION SETUP

### Prompt 0.1 — Project Scaffolding
```
GEMINI CLI:
────────────
Task: Create the complete project scaffold for verif-ai-backend.

Read GEMINI.md for the exact folder structure required.

Create these files with correct content:

1. requirements.txt — include ALL packages:
   fastapi, uvicorn[standard], motor, beanie, firebase-admin, pydantic>=2.7,
   pydantic-settings, langchain>=0.3, langchain-google-genai>=2.0,
   langchain-community, langgraph>=0.2, langchain-mcp-adapters, langsmith,
   deepagents, pdfplumber, pypdf, pytesseract, Pillow, PyGithub, radon,
   httpx, aiofiles, python-multipart, python-dotenv

2. .env.example — all variable names with empty values, include comments

3. .gitignore — Python standard + .env + firebase-credentials.json

4. app/__init__.py, app/api/__init__.py, app/api/v1/__init__.py,
   app/services/__init__.py, app/services/graph/__init__.py,
   app/services/tools/__init__.py, app/models/__init__.py,
   app/schemas/__init__.py, app/core/__init__.py
   (all empty __init__.py files)

5. app/core/config.py — Pydantic BaseSettings reading all env vars from GEMINI.md

After creating all files:
@git commit -m "feat: project scaffold + requirements" && git push

List every file created.
```

### Prompt 0.2 — Database + Firebase Core
```
GEMINI CLI:
────────────
Task: Build the core infrastructure files.

Files to create:

1. app/core/database.py
   - Async Motor client connecting to MONGODB_URI
   - GridFS setup for "resumes" and "certificates" buckets
   - Beanie initialization with all document models
   - get_motor_client() and get_gridfs(bucket_name) helper functions
   - Use lifespan context manager (not @app.on_event which is deprecated)

2. app/core/firebase.py
   - Initialize Firebase Admin SDK from FIREBASE_CREDENTIALS_JSON env var
   - Initialize Firestore client: db = firestore.client()
   - verify_firebase_token(creds) → async dependency that returns decoded dict
   - require_student(user) → dependency that checks role == "student"
   - require_recruiter(user) → dependency that checks role == "recruiter"
   - get_firestore() helper that returns the db client
   - Handle case where FIREBASE_CREDENTIALS_JSON is a JSON string (parse it)

3. app/core/langchain_setup.py
   - get_gemini_flash() → ChatGoogleGenerativeAI(model="gemini-1.5-flash", streaming=True, temperature=0.1)
   - get_gemini_vision() → ChatGoogleGenerativeAI(model="gemini-1.5-pro", streaming=True, temperature=0.1)
   - Configure LangSmith from LANGCHAIN_TRACING_V2, LANGCHAIN_API_KEY env vars
   - Both functions must use GEMINI_API_KEY from env

4. app/main.py
   - FastAPI app with lifespan context manager
   - Lifespan: init MongoDB Motor + Beanie + Firebase in startup
   - CORS: allow ALLOWED_ORIGINS from env, allow all methods and headers
   - Include routers (even if files don't exist yet, use try/except import)
   - Health endpoint: GET /health → {"status": "healthy", "mongodb": "...", "firebase": "..."}
   - GET /health actually tests the connections, returns real status

After all files created:
@git commit -m "feat: core infrastructure - database, firebase, langchain" && git push
List every file created.
```

---

## PHASE 1: AUTHENTICATION

### Prompt 1.1 — Auth Models + Schemas
```
GEMINI CLI:
────────────
Task: Build auth models and schemas.

1. app/models/user.py
   - Beanie Document class "User" mapping to MongoDB "users" collection
   - Fields: firebase_uid (str, unique), email (str), role (str: "student"|"recruiter"),
     display_name (Optional[str]), created_at (datetime), updated_at (datetime)
   - Class Settings: name = "users", indexes on firebase_uid and email

2. app/schemas/auth.py
   - UserSyncRequest: firebase_uid, email, role, display_name (optional)
   - UserResponse: id, firebase_uid, email, role, display_name, created_at
   - All using Pydantic v2 BaseModel

Update contracts/CONTRACT.md with:
- POST /api/v1/auth/sync endpoint spec
- GET /api/v1/auth/me endpoint spec

@git commit -m "feat: auth models and schemas" && git push
```

### Prompt 1.2 — Auth Endpoints
```
GEMINI CLI:
────────────
Task: Build app/api/v1/auth.py with these endpoints:

POST /api/v1/auth/sync
- Protected: requires verify_firebase_token
- Body: UserSyncRequest
- Logic: Check if user exists in MongoDB by firebase_uid, if not create it
- Also upsert to Firestore /users/{firebase_uid} with same data
- Return UserResponse (201 if created, 200 if updated)

GET /api/v1/auth/me
- Protected: requires verify_firebase_token
- Return current user's profile from MongoDB

PUT /api/v1/auth/role
- Protected: requires verify_firebase_token
- Body: {"role": "student" | "recruiter"}
- Update role in both MongoDB and Firestore
- Used during onboarding role selection

GET /api/v1/auth/health
- Public: no auth required
- Returns {"firebase": "connected", "mongodb": "connected"}

Every endpoint must:
- Use async def
- Have proper HTTPException on errors
- Return {"success": bool, "data": {}, "message": ""}

After writing, update contracts/CONTRACT.md with all 4 endpoints.
@git commit -m "feat: auth endpoints" && git push
```

---

## PHASE 2: FILE UPLOAD

### Prompt 2.1 — Document Models + Upload
```
GEMINI CLI:
────────────
Task: Build file upload system using MongoDB GridFS.

1. app/models/document.py
   - Beanie Document class "Document" → "documents" collection
   - Fields: firebase_uid (str), type ("resume"|"certificate"|"github"),
     gridfs_id (Optional[PydanticObjectId]), github_url (Optional[str]),
     filename (Optional[str]), mime_type (Optional[str]),
     hash_sha256 (str), size_bytes (int), status ("pending"|"analyzing"|"done"|"failed"),
     uploaded_at (datetime)

2. app/schemas/document.py
   - UploadResponse: document_id, type, hash_sha256, status, filename
   - GitHubSubmitRequest: github_url (str, must start with https://github.com/), student_uid

3. app/api/v1/documents.py with these endpoints:

POST /api/v1/documents/upload
- Protected: require_student
- multipart/form-data: file (UploadFile), type ("resume"|"certificate")
- Validation:
  * type must be "resume" or "certificate"
  * mime_type must be in allowed list: application/pdf, image/jpeg, image/png, image/jpg
  * file size must be <= 10MB (10 * 1024 * 1024 bytes)
  * Check mime type from file content (not just extension) using python-magic or file header bytes
- Processing:
  * Generate SHA-256 hash of file bytes
  * Store in GridFS: bucket = "resumes" if type==resume else "certificates"
  * Create Document record in MongoDB
- Return UploadResponse

POST /api/v1/documents/github
- Protected: require_student
- Body: GitHubSubmitRequest
- Validate URL starts with "https://github.com/"
- Extract username from URL, verify it's a valid GitHub username format
- Create Document record with type="github", github_url field set
- Return UploadResponse

GET /api/v1/documents/my
- Protected: require_student
- Return list of current student's uploaded documents

After writing, update contracts/CONTRACT.md with all 3 endpoints.
@git commit -m "feat: document upload with GridFS" && git push
```

---

## PHASE 3: LANGGRAPH AGENT SYSTEM

### Prompt 3.1 — Shared State + Tools
```
GEMINI CLI:
────────────
Task: Build the LangGraph shared state and all tool functions.

1. app/services/graph/state.py
   Build VerificationState TypedDict exactly as defined in GEMINI.md.
   Also define AgentFlag and ResearchStep Pydantic models here.
   Also define final result Pydantic schemas:
   - ResumeAgentResult(BaseModel)
   - CertAgentResult(BaseModel)
   - GitHubAgentResult(BaseModel)
   Each with all fields from GEMINI.md.

2. app/services/tools/stylometry_tools.py
   - compute_burstiness(text: str) -> float
     Split text into sentences, compute stdev/mean of sentence lengths.
     Returns: human avg ~0.85+, AI avg ~0.23
   - compute_type_token_ratio(text: str) -> float
     unique_words / total_words. Human ~0.72, AI ~0.58
   - compute_avg_sentence_length(text: str) -> float
   - analyze_text_locally(text: str) -> dict
     Returns all 3 signals above in one dict

3. app/services/tools/pdf_tools.py
   - LangChain @tool: extract_pdf_text(gridfs_doc_id: str) -> str
     Retrieve bytes from GridFS → pdfplumber → return extracted text
   - LangChain @tool: extract_pdf_metadata(gridfs_doc_id: str) -> dict
     pypdf PdfReader → return creation_date, modification_date, author, producer
   - Both must be async, wrap DB calls properly

4. app/services/tools/image_tools.py
   - error_level_analysis(image_bytes: bytes, quality: int = 95) -> float
     Re-compress at quality 95 → diff → np.std of difference. Higher = more editing.
   - LangChain @tool: ocr_image(gridfs_doc_id: str) -> str
     Retrieve from GridFS → pytesseract.image_to_string → return text
   - LangChain @tool: analyze_certificate_image(gridfs_doc_id: str) -> dict
     Retrieve → run ELA → run OCR → return {ela_score, ocr_text, suspicious: bool}

5. app/services/tools/github_tools.py
   - LangChain @tool: get_github_profile(github_url: str) -> dict
     Extract username → PyGithub → return profile dict (account_age_days, bio, followers, public_repos)
   - LangChain @tool: analyze_github_repos(github_url: str) -> dict
     Get all repos → compute fork_ratio, language_distribution, readme_only_count, avg_stars
   - LangChain @tool: analyze_commit_patterns(github_url: str) -> dict
     Commits from top 10 repos → compute burst_score, commit_msg_quality_score, hour_distribution
   - compute_burst_score(dates: list) -> float (helper, not a tool)
   - compute_commit_message_quality(messages: list) -> float (helper, not a tool)

All tools must handle exceptions gracefully and return meaningful error dicts on failure.

@git commit -m "feat: LangGraph state + all agent tools" && git push
```

### Prompt 3.2 — Resume Agent Node
```
GEMINI CLI:
────────────
Task: Build app/services/graph/resume_node.py — the Resume Fraud Detection Agent.

This is a LangChain ReAct agent using Gemini 1.5 Flash.
Read contracts/resume-agent.md for the system prompt.

The node function signature:
  async def resume_agent_node(state: VerificationState) -> dict

Pipeline:
1. Retrieve resume_doc_id from state
2. Call extract_pdf_text tool to get text
3. Call analyze_text_locally (stylometry — no API) to get burstiness, TTR, avg_sentence_len
4. Extract structured data from text: skills[], education[], experience[], timeline[]
5. Build Gemini prompt that includes: resume text + stylometry signals + instruction to verify via web search
6. Create LangChain agent with tools: [extract_pdf_text, web_search_tool]
   For web_search_tool: use langchain-mcp-adapters connecting to brave-search MCP OR
   use a simple httpx call to Brave Search API if MCP not available
7. Stream agent via astream_events v3 — collect all research steps
8. Force structured output: ResumeAgentResult Pydantic schema
9. Save research steps to Firestore /research_logs/{log_id}
10. Return state update: {"resume_result": result.dict(), "research_logs": [steps], "completed_agents": ["resume"]}

Fallback: if Gemini fails (timeout/error), return neutral scores (all 50.0) and mark completed_agents

The system prompt for the agent (also save to contracts/resume-agent.md):
"""
You are an expert resume fraud investigator with access to web search.
For EVERY claim in the resume, search the web to verify it.
Log every search: what you searched, what URL you found, what you concluded.
Focus on: AI-generated writing patterns, skill inflation, timeline impossibilities.
Return STRICT JSON matching the ResumeAgentResult schema. No markdown, no explanation.
"""

@git commit -m "feat: resume agent node with LangGraph + Gemini" && git push
```

### Prompt 3.3 — Certificate Agent Node
```
GEMINI CLI:
────────────
Task: Build app/services/graph/certificate_node.py — Certificate Forgery Detection.

This agent uses Gemini 1.5 Pro (vision capable).

Pipeline for each certificate document_id:
1. Retrieve file from GridFS
2. Detect mime type from file header bytes
3. If PDF: run extract_pdf_metadata + pdfplumber text
   If image (jpg/png): run ELA analysis + pytesseract OCR

4. Encode image as base64 for Gemini Vision
5. Build prompt with:
   - Image bytes (base64)
   - OCR text
   - ELA score and interpretation
   - PDF metadata if applicable
   - Instruction: verify issuer via web search, check template authenticity

6. Call Gemini Vision with structured output: CertAgentResult
7. Stream via astream_events v3, collect research steps
8. Save to Firestore /research_logs/

The system prompt (save to contracts/certificate-agent.md):
"""
You are an expert document forensics examiner.
For each certificate: identify the issuing organization, search the web to verify it exists,
check if the course/program actually exists at that institution.
Analyze: visual inconsistencies, font irregularities, ELA score, metadata anomalies.
Log every verification step with sources.
Return STRICT JSON matching CertAgentResult schema.
"""

9. Aggregate results from all certificates
10. Return: {"cert_result": aggregated_result, "research_logs": steps, "completed_agents": ["certificate"]}

Handle multiple certificates: run them in parallel with asyncio.gather, aggregate scores.

@git commit -m "feat: certificate agent node with Gemini Vision + ELA" && git push
```

### Prompt 3.4 — GitHub Agent Node
```
GEMINI CLI:
────────────
Task: Build app/services/graph/github_node.py — GitHub OSINT + Code Verification.

This is the most powerful agent. Use LangChain with all GitHub tools.

Pipeline:
1. Extract github_url from state
2. Call get_github_profile tool → account age, bio, follower count
3. Call analyze_github_repos tool → fork_ratio, languages, readme_only_count
4. Call analyze_commit_patterns tool → burst_score, message_quality
5. Extract 3 code samples from top non-forked repos via PyGithub

6. CRITICAL: Read state["resume_result"] if available:
   - Get skills claimed in resume
   - Compare with languages found in GitHub
   - Pass this comparison as context to Gemini prompt

7. Build Gemini prompt with all gathered data + resume comparison context
8. Create LangChain agent with web_search, get_github_profile, analyze_github_repos tools
9. Stream via astream_events v3

The system prompt (save to contracts/github-agent.md):
"""
You are a senior cybersecurity engineer and OSINT investigator.
Analyze this GitHub profile against the claimed skills and experience.
Look for: copy-paste code, fork-heavy profiles, burst commits before job applications,
GitHub account age vs claimed experience, skills on resume missing from GitHub.
Cross-reference: do the commit dates align with the resume timeline?
Log every search and finding with sources.
Return STRICT JSON matching GitHubAgentResult schema.
"""

10. Return: {"github_result": result, "research_logs": steps, "completed_agents": ["github"]}

@git commit -m "feat: GitHub OSINT agent with cross-state reference" && git push
```

### Prompt 3.5 — Cross-Reference + Final Decision + Graph Builder
```
GEMINI CLI:
────────────
Task: Build the remaining graph nodes and assemble the full LangGraph pipeline.

1. app/services/graph/cross_reference.py
   Function: async def cross_reference_node(state: VerificationState) -> dict
   
   Perform these cross-checks using state data (no LLM needed here — pure logic):
   a. Resume skills vs GitHub languages:
      For each skill in resume_result.skills_claimed:
        if skill not in github_result.languages_used: add HIGH_FLAG
   b. Resume dates vs GitHub first commits:
      For each skill with claimed start date:
        if github shows first commit AFTER claimed date: add HIGH_FLAG
   c. Certificate courses vs GitHub evidence:
      For each cert course: if no related GitHub project found: add MEDIUM_FLAG
   
   Add a research_log step for each cross-check performed.
   Return: {"cross_ref_findings": findings_list, "research_logs": [cross_ref_steps]}

2. app/services/graph/final_decision.py
   Function: async def final_decision_node(state: VerificationState) -> dict
   
   - Calculate trust_score = resume×0.40 + cert×0.35 + github×0.25
   - Determine verdict:
     ≥80 → AUTHENTIC | 60-79 → FLAGGED | 35-59 → SUSPICIOUS | <35 → FAKE
   - Save to Firestore:
     * /verifications/{new_id}: full result with all scores
     * /profiles/{student_uid}: update trust_score + verification_id
   - Return: {"overall_trust_score": score, "verdict": verdict}

3. app/services/graph/graph_builder.py
   - Build complete StateGraph as defined in GEMINI.md
   - Supervisor node: just validates state has all required input fields
   - Parallel dispatch: supervisor → resume_node, cert_node, github_node simultaneously
   - Conditional edge after each agent: check if completed_agents has all 3, if yes → cross_reference
   - Linear: cross_reference → final_decision → END
   - app = workflow.compile() at bottom
   - Export: get_app() function that returns the compiled graph

4. app/services/streaming.py
   - stream_graph_events(app, initial_state: dict) -> AsyncGenerator
   - Implements the full astream_events v3 pattern from GEMINI.md
   - Yields properly typed WebSocket event dicts
   - Handles: thinking_token, research_step_start, research_step_complete, analysis_complete, error

5. app/services/trust_score.py
   - calculate_trust_score(resume: float, cert: float, github: float) -> float
   - get_verdict(score: float) -> str

After building all files:
@git commit -m "feat: complete LangGraph pipeline - cross-ref + final decision + graph builder" && git push
```

### Prompt 3.6 — Analysis API Endpoint
```
GEMINI CLI:
────────────
Task: Build app/api/v1/analysis.py — the main analysis trigger and WebSocket stream.

Endpoints needed:

POST /api/v1/analysis/start
- Protected: require_student
- Body: {student_uid, resume_document_id, certificate_document_ids[], github_url}
- Validation: verify all document_ids exist and belong to this student
- Start LangGraph pipeline in background (asyncio.create_task)
- Update all documents status to "analyzing" in MongoDB
- Return 202: {job_id, student_uid, status: "analyzing", websocket_url}

WebSocket /api/v1/analysis/stream/{job_id}
- Auth: query param ?token=<firebase_jwt>
- Connect → verify token → get analysis job
- Stream events from LangGraph pipeline using stream_graph_events()
- Send each event as JSON string over WebSocket
- Close connection gracefully after "analysis_complete" event
- Handle disconnection: cancel the LangGraph task

GET /api/v1/analysis/result/{student_uid}
- Protected: verify_firebase_token (student sees own, recruiter sees if profile is public)
- Fetch from Firestore /verifications/ where student_uid matches
- Return full verification result with all agent scores and flags

GET /api/v1/analysis/logs/{result_id}
- Protected: verify_firebase_token
- Fetch from Firestore /research_logs/{result_id}
- Return full research log with all steps

Update contracts/CONTRACT.md with all 4 endpoints including WebSocket message format.
@git commit -m "feat: analysis API - trigger + WebSocket stream + results" && git push
```

---

## PHASE 4: DISCOVERY SYSTEM

### Prompt 4.1 — Student Profile Publishing
```
GEMINI CLI:
────────────
Task: Build the student profile publish/discovery system.

1. app/schemas/profile.py
   - StudentProfileUpdate: skills[], domain (str), location (str), bio (str), is_public (bool)
   - PublicProfile: uid, display_name, trust_score, verdict, skills[], domain,
     location, bio, verified_at, verification_summary

2. app/schemas/discover.py
   - SearchQuery: skills (list, optional), min_trust (float default 0),
     domain (str optional), location (str optional), limit (int default 20)
   - SearchResult: profiles (list[PublicProfile]), total, query_used

3. app/services/discovery_service.py
   - publish_profile(firebase_uid, update: StudentProfileUpdate) → saves to Firestore /profiles/
   - get_public_profile(firebase_uid) → fetch from Firestore, verify is_public=true
   - search_profiles(query: SearchQuery) → Firestore composite query
   - shortlist_student(recruiter_uid, student_uid) → add to /shortlists/{recruiter_uid}
   - get_shortlist(recruiter_uid) → fetch shortlisted student profiles

4. app/api/v1/profile.py
   PUT /api/v1/profile/update     → require_student → update /profiles/{uid}
   POST /api/v1/profile/publish   → require_student → set is_public=true
   POST /api/v1/profile/unpublish → require_student → set is_public=false
   GET /api/v1/profile/{uid}      → public endpoint → return PublicProfile if is_public=true

5. app/api/v1/discover.py
   GET /api/v1/discover           → require_recruiter → browse all public profiles (paginated)
   GET /api/v1/discover/search    → require_recruiter → query params: skills, min_trust, domain
   POST /api/v1/discover/shortlist/{uid} → require_recruiter → shortlist a student
   GET /api/v1/discover/shortlist        → require_recruiter → get own shortlist

NOTE: Only students with is_public=true AND verification_status="done" appear in discovery.
NOTE: Trust score is the primary sort field — highest first.

Update contracts/CONTRACT.md with all 8 endpoints.
@git commit -m "feat: student profile publishing + recruiter discovery system" && git push
```

### Prompt 4.2 — Verification Results Endpoint
```
GEMINI CLI:
────────────
Task: Build app/api/v1/verification.py.

GET /api/v1/verification/my
- require_student
- Return current student's latest verification from Firestore

GET /api/v1/verification/student/{uid}
- require_recruiter
- Check if student profile is_public=true, if not return 403
- Return PublicProfile + full verification scores + flags summary
- Return research_logs summary (not full logs — just summary_stats)

GET /api/v1/verification/logs/{result_id}
- require_recruiter OR the student who owns it
- Return full research_logs document from Firestore
- This is what powers the side panel in the recruiter dashboard

Also seed the Firestore with test data:
@firebase seed 5 student profiles with these trust scores:
- clean@test.com: trust_score=88, verdict=AUTHENTIC, is_public=true
- suspicious@test.com: trust_score=55, verdict=FLAGGED, is_public=true
- fakecert@test.com: trust_score=42, verdict=SUSPICIOUS, is_public=true
- ghostgithub@test.com: trust_score=33, verdict=SUSPICIOUS, is_public=true
- allfake@test.com: trust_score=18, verdict=FAKE, is_public=true

Use @mongodb to insert the corresponding document records.

Update contracts/CONTRACT.md.
@git commit -m "feat: verification results endpoints + seed test data" && git push
```

---

## PHASE 5: TESTING

### Prompt 5.1 — Test Infrastructure
```
OPENCODE (deepseek-r1:14b):
────────────────────────────
Task: Build the complete test infrastructure.

1. tests/conftest.py
   Create all fixtures as described in TESTING_GUIDE.md:
   - async client fixture using httpx AsyncClient
   - valid_firebase_token mock fixture (patches verify_firebase_token)
   - recruiter_firebase_token mock fixture
   - mock_gemini_flash fixture (patches ChatGoogleGenerativeAI)
   - mock_firestore fixture (in-memory Firestore mock using unittest.mock)
   - sample_resume_pdf fixture (minimal valid PDF bytes)
   - sample_cert_image fixture (PIL-generated minimal JPEG)

2. tests/test_auth.py
   Test all 4 auth endpoints:
   - test_sync_new_user → expect 201
   - test_sync_existing_user → expect 200
   - test_sync_without_token → expect 401
   - test_invalid_role → expect 422
   - test_get_me → expect 200 with user data

3. tests/test_documents.py
   - test_upload_valid_resume
   - test_upload_valid_certificate_image
   - test_upload_oversized_file → expect 400
   - test_upload_invalid_type (exe) → expect 400
   - test_submit_valid_github_url
   - test_submit_invalid_github_url → expect 400

Run after writing:
  pytest tests/test_auth.py tests/test_documents.py -v

Fix any failures before moving on.
@git commit -m "test: auth + documents test suites" && git push
```

### Prompt 5.2 — Agent Tests
```
OPENCODE (deepseek-coder-v2:16b):
──────────────────────────────────
Task: Build agent-level tests.

1. tests/test_resume_node.py
   - test_resume_node_happy_path: valid state → result has all required fields
   - test_resume_node_gemini_timeout: mock Gemini timeout → fallback score 50
   - test_burstiness_human_vs_ai: human text scores higher burstiness than AI text
   - test_research_logs_saved: after node runs, research_logs is non-empty in returned state

2. tests/test_certificate_node.py
   - test_cert_node_pdf_pipeline: PDF document → runs metadata extraction
   - test_cert_node_image_pipeline: JPEG document → runs ELA + OCR
   - test_ela_detects_edited_image: create a modified JPEG → ELA score > threshold
   - test_ela_on_clean_image: clean JPEG → low ELA score

3. tests/test_github_node.py
   - test_github_node_happy_path: valid URL → result has all required fields
   - test_burst_score_consistent_developer: evenly spaced dates → moderate burst score
   - test_burst_score_cramming: 50 commits in 1 week then nothing → low burst score
   - test_commit_message_quality_real: real commit messages → high quality score
   - test_commit_message_quality_fake: "update", "edit", "asdf" → low quality score

4. tests/test_graph.py
   - test_full_pipeline_completes: all 3 agents return results, trust_score calculated
   - test_single_agent_failure_doesnt_crash: mock github_node to raise Exception → still completes
   - test_trust_score_formula: assert resume×0.40 + cert×0.35 + github×0.25
   - test_cross_ref_detects_skill_mismatch: resume claims React, GitHub has none → HIGH_FLAG
   - test_verdict_assignment: score 85 → AUTHENTIC, 65 → FLAGGED, 45 → SUSPICIOUS, 20 → FAKE

5. tests/test_discover.py
   - test_search_returns_only_public_profiles
   - test_search_filters_by_min_trust
   - test_recruiter_can_shortlist
   - test_student_cannot_access_discover → expect 403

Run all:
  pytest tests/ -v --tb=short

Report failures. Fix them without being asked.
@git commit -m "test: complete agent + graph + discovery test suites" && git push
```

---

## PHASE 6: DEPLOYMENT

### Prompt 6.1 — Pre-Deploy Checklist
```
GEMINI CLI:
────────────
Task: Prepare for production deployment.

1. Create render.yaml with config from GEMINI.md

2. Create .env.example with all variable names (no values)

3. Verify CORS configuration in main.py:
   - ALLOWED_ORIGINS must include the Vercel frontend URL
   - Add: https://verif-ai-frontend.vercel.app to ALLOWED_ORIGINS
   - Also allow localhost:3000 for development

4. Create a /health endpoint that:
   - Tests MongoDB connection: await db.command("ping")
   - Tests Firebase: verify firebase_admin.get_app() exists
   - Tests Gemini: make a minimal test call
   - Returns: {"status": "healthy", "checks": {mongodb, firebase, gemini}}

5. Add production error handling to main.py:
   - @app.exception_handler(Exception) → return 500 with structured error
   - Never expose stack traces in production (check ENVIRONMENT != "development")

6. Run final test suite:
   pytest tests/ -v
   All tests must pass before deploying.

List all files modified.
```

### Prompt 6.2 — Deploy to Render
```
GEMINI CLI:
────────────
Task: Deploy verif-ai-backend to Render using MCP.

Using @render MCP tool:

1. Create new Web Service on Render:
   Name: verif-ai-backend
   Runtime: Python 3
   Build command: pip install -r requirements.txt
   Start command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   Region: Singapore (closest to India)

2. Set all environment variables from .env (use @render setenv for each):
   - MONGODB_URI
   - MONGODB_DB_NAME
   - FIREBASE_PROJECT_ID
   - FIREBASE_CREDENTIALS_JSON (the full JSON as string)
   - GEMINI_API_KEY
   - GOOGLE_API_KEY
   - GITHUB_TOKEN
   - BRAVE_API_KEY
   - LANGCHAIN_API_KEY
   - LANGCHAIN_TRACING_V2
   - LANGCHAIN_PROJECT
   - ALLOWED_ORIGINS (include the Vercel URL)
   - ENVIRONMENT=production

3. Trigger deploy and watch logs

4. After deploy completes:
   - Test: GET https://verif-ai-backend.onrender.com/health
   - Expected: {"status": "healthy"}
   - Test: POST auth/sync with a valid Firebase token

5. Update contracts/CONTRACT.md with production URL
6. Message frontend dev: "TYPE: DEPLOYED | Backend live at https://verif-ai-backend.onrender.com"

@git commit -m "deploy: production deployment to Render" && git push
```

---

## QUICK REFERENCE: JUDGE QUESTIONS + YOUR ANSWERS

Prepare these answers. Judges WILL ask these.

**Q: "How does a recruiter find a student?"**
> "Students publish their profile after analysis — it appears in our searchable discovery feed. Recruiters filter by skills, trust score, and domain. Students can also share a direct profile link. Think of it like LinkedIn meets fraud detection."

**Q: "What if a student doesn't want to be found?"**
> "Profile publishing is opt-in. By default, profiles are private. Students toggle is_public=true when they want to be discovered. They can unpublish anytime."

**Q: "Can't students game the system? Just use a real GitHub?"**
> "Yes, and that's fine — it means they have real skills. The fraud we're detecting is misrepresentation: claiming skills you don't have, certificates you didn't earn, timelines that are impossible. The system rewards authentic candidates."

**Q: "How accurate is the AI detection?"**
> "Each agent provides specific evidence — exact URLs visited, exact findings. Recruiters aren't forced to trust a black-box score. They see the AI's full reasoning trail and make their own judgment. Our system reduces verification time from 3 days to 60 seconds, not replaces human judgment."

**Q: "What about privacy? Are resumes stored securely?"**
> "Files are stored in MongoDB GridFS with SHA-256 integrity hashes. Results are in Firebase behind Firebase Auth JWT — only the owner and verified recruiters see them. Students control their own visibility."

**Q: "Why LangGraph instead of just calling Gemini?"**
> "LangGraph gives us shared state between agents. The GitHub agent's findings feed into the Resume agent's evaluation. That cross-agent reasoning is only possible with a stateful graph — you can't do it with independent API calls."

---

*Use every prompt verbatim. Don't improvise mid-prompt. If the agent gets stuck, paste the relevant section of GEMINI.md as additional context.*
