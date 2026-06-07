# API Endpoints

## Authentication (`/auth`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/student/register` | Firebase token | Register student → returns JWT pair + sets cookies |
| POST | `/auth/recruiter/register` | Firebase token | Register recruiter → returns JWT pair + sets cookies |
| POST | `/auth/login` | Firebase token | Login via Firebase → returns JWT pair + sets cookies |
| POST | `/auth/refresh` | Refresh token (body or cookie) | Rotate refresh token → new JWT pair + sets cookies |
| GET | `/auth/me` | Bearer token or cookie | Restore session; auto-refreshes if access token expired |
| POST | `/auth/logout` | Bearer token or cookie | Blacklist both tokens + clears cookies |

### Request/Response Examples

**POST /auth/student/register**
```json
// Request
{ "full_name": "John Doe", "email": "john@example.com", "password": "secret123", "college_name": "MIT", "graduation_year": 2026 }

// Response
{ "success": true, "message": "Student registered successfully", "data": { "access_token": "eyJ...", "refresh_token": "eyJ...", "user": { "id": "...", "email": "john@example.com", "role": "student" } } }
```

**POST /auth/recruiter/register**
```json
// Request
{ "company_name": "Acme Corp", "recruiter_name": "Jane Smith", "email": "jane@acme.com", "password": "secret123" }

// Response
{ "success": true, "message": "Recruiter registered successfully", "data": { "access_token": "eyJ...", "refresh_token": "eyJ...", "user": { "id": "...", "email": "jane@acme.com", "role": "recruiter" } } }
```

**POST /auth/login**
```json
// Request
{ "email": "john@example.com", "password": "secret123" }

// Response
{ "success": true, "message": "Login successful", "data": { "access_token": "eyJ...", "refresh_token": "eyJ...", "user": { "id": "...", "email": "john@example.com", "role": "student" } } }
```

**POST /auth/refresh**
```json
// Request
{ "refresh_token": "eyJ..." }

// Response
{ "success": true, "message": "Token refreshed successfully", "data": { "access_token": "eyJ...", "refresh_token": "eyJ..." } }
```

**GET /auth/me**
```json
// Response
{ "success": true, "message": "User session restored", "data": { "id": "...", "email": "john@example.com", "role": "student" } }
```

**POST /auth/logout**
```json
// Response
{ "success": true, "message": "Logged out successfully", "data": {} }
```

### Cookie behavior
On register/login/refresh, the backend sets two HTTP-only cookies:
- `access_token` (path=/) — access token TTL
- `refresh_token` (path=/) — refresh token TTL

Cookies are sent on all cross-origin requests when `COOKIE_SAMESITE` and `COOKIE_SECURE` are configured appropriately (use `SameSite=None; Secure=True` for production cross-origin; `SameSite=Lax` for same-origin or localhost).

### Session persistence (page refresh)
1. On page load, the frontend calls `GET /auth/me`
2. If the `access_token` cookie is valid → user session restored
3. If the `access_token` cookie expired but `refresh_token` cookie is valid → `/auth/me` auto-refreshes the access token, sets new cookies, and returns user data
4. If both tokens expired → `TOKEN_EXPIRED` error, user sees login screen

### Auth for all endpoints
All protected endpoints (`/student/*`, `/recruiter/*`, `/admin/*`) now support authentication via:
- `Authorization: Bearer <access_token>` header (preferred for programmatic/API clients)
- `access_token` HTTP-only cookie (used by browser after login)
If no bearer header is present, the `access_token` cookie is read automatically. This means page refreshes preserve the session across all endpoints, not just `/auth/me`.

## Students (`/student`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/student/profile` | student | Get profile |
| PUT | `/student/profile` | student | Update profile |
| POST | `/student/profile/photo` | student | Upload photo (multipart) |
| GET | `/student/profile/photo` | student | Fetch photo |
| GET | `/student/applications` | student | List applications |
| GET | `/student/applications/{id}` | student | Application detail |
| POST | `/student/saved-companies?company_id=` | student | Save company |
| GET | `/student/saved-companies` | student | List saved companies |
| DELETE | `/student/saved-companies/{company_id}` | student | Remove saved company |

### Request/Response Examples

**GET /student/profile**
```json
// Response
{ "success": true, "message": "Student profile retrieved", "data": { "id": "...", "full_name": "John Doe", "email": "john@example.com", "college_name": "MIT", "branch": "CS", "graduation_year": 2026, "skills": "Python, React", "role": "student" } }
```

**PUT /student/profile**
```json
// Request
{ "full_name": "John Updated", "skills": "Python, React, Go" }

// Response
{ "success": true, "message": "Profile updated successfully", "data": { "full_name": "John Updated", "skills": "Python, React, Go", "role": "student" } }
```

**POST /student/profile/photo** — `multipart/form-data` with `photo` field
```json
// Response
{ "success": true, "message": "Profile photo uploaded successfully", "data": { "photo_url": "/student/profile/photo" } }
```

**GET /student/profile/photo** — Returns raw image binary

**GET /student/applications?page=1&page_size=20**
```json
// Response
{ "success": true, "message": "Applications retrieved successfully", "data": { "applications": [{ "id": "...", "status": "draft", "posting_id": "...", "created_at": "..." }], "total": 1, "page": 1, "page_size": 20 } }
```

**GET /student/applications/{id}**
```json
// Response
{ "success": true, "message": "Application retrieved successfully", "data": { "id": "...", "status": "submitted", "resume_file_id": "...", "submitted_at": "..." } }
```

**POST /student/saved-companies?company_id=abc123**
```json
// Response
{ "success": true, "message": "Company saved successfully", "data": { "company_id": "abc123", "student_id": "...", "saved_at": "..." } }
```

**GET /student/saved-companies**
```json
// Response
{ "success": true, "message": "Saved companies retrieved successfully", "data": { "saved_companies": [{ "company_id": "abc123", "company_name": "Acme Corp" }], "total": 1 } }
```

**DELETE /student/saved-companies/{company_id}**
```json
// Response
{ "success": true, "message": "Company removed from saved list", "data": {} }
```

## Recruiters (`/recruiter`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/recruiter/profile` | recruiter | Get profile |
| PUT | `/recruiter/profile` | recruiter | Update profile |
| DELETE | `/recruiter/profile` | recruiter | Delete profile |
| POST | `/recruiter/companies` | recruiter | Create company profile |
| GET | `/recruiter/companies` | recruiter | Get company profile |
| PUT | `/recruiter/companies/{id}` | recruiter | Update company profile |
| POST | `/recruiter/postings` | recruiter | Create posting |
| GET | `/recruiter/postings` | recruiter | List postings |
| PUT | `/recruiter/postings/{id}` | recruiter | Update posting |
| DELETE | `/recruiter/postings/{id}` | recruiter | Delete posting |
| GET | `/recruiter/applications` | recruiter | List applications |
| GET | `/recruiter/applications/{id}` | recruiter | Application detail |
| PATCH | `/recruiter/applications/{id}/status` | recruiter | Update status |

### Request/Response Examples

**GET /recruiter/profile**
```json
// Response
{ "success": true, "message": "Recruiter profile retrieved", "data": { "id": "...", "company_name": "Acme Corp", "recruiter_name": "Jane Smith", "email": "jane@acme.com", "role": "recruiter" } }
```

**PUT /recruiter/profile**
```json
// Request
{ "recruiter_name": "Jane Updated", "designation": "Senior Recruiter" }

// Response
{ "success": true, "message": "Profile updated successfully", "data": { "recruiter_name": "Jane Updated", "designation": "Senior Recruiter", "role": "recruiter" } }
```

**DELETE /recruiter/profile**
```json
// Response
{ "success": true, "message": "Profile deleted successfully", "data": {} }
```

**POST /recruiter/companies**
```json
// Request
{ "company_name": "Acme Corp", "hiring_status": "hiring", "tech_stack": ["Python", "React"], "location": "San Francisco" }

// Response
{ "success": true, "message": "Company profile created successfully", "data": { "id": "...", "company_name": "Acme Corp", "hiring_status": "hiring", "tech_stack": ["Python", "React"], "location": "San Francisco", "is_active": true } }
```

**GET /recruiter/companies**
```json
// Response
{ "success": true, "message": "Company profile retrieved", "data": { "id": "...", "company_name": "Acme Corp", "hiring_status": "hiring" } }
```

**PUT /recruiter/companies/{id}**
```json
// Request
{ "hiring_status": "paused", "tech_stack": ["Python", "React", "Go"] }

// Response
{ "success": true, "message": "Company profile updated successfully", "data": { "id": "...", "company_name": "Acme Corp", "hiring_status": "paused", "tech_stack": ["Python", "React", "Go"] } }
```

**POST /recruiter/postings**
```json
// Request
{ "title": "Software Engineer", "type": "job", "description": "Build awesome things", "location": "Remote", "is_remote": true }

// Response
{ "success": true, "message": "Job posting created successfully", "data": { "id": "...", "title": "Software Engineer", "type": "job", "status": "open", "is_remote": true } }
```

**GET /recruiter/postings**
```json
// Response
{ "success": true, "message": "Postings retrieved successfully", "data": { "postings": [{ "id": "...", "title": "Software Engineer", "status": "open" }], "total": 1 } }
```

**PUT /recruiter/postings/{id}**
```json
// Request
{ "status": "closed", "description": "Updated description" }

// Response
{ "success": true, "message": "Job posting updated successfully", "data": { "id": "...", "title": "Software Engineer", "status": "closed" } }
```

**DELETE /recruiter/postings/{id}**
```json
// Response
{ "success": true, "message": "Job posting deleted successfully", "data": {} }
```

**GET /recruiter/applications?page=1&page_size=20**
```json
// Response
{ "success": true, "message": "Applications retrieved successfully", "data": { "applications": [{ "id": "...", "student_name": "John Doe", "posting_title": "Software Engineer", "status": "submitted" }], "total": 1, "page": 1, "page_size": 20 } }
```

**GET /recruiter/applications/{id}**
```json
// Response
{ "success": true, "message": "Application retrieved successfully", "data": { "id": "...", "student_name": "John Doe", "college_name": "MIT", "status": "submitted", "resume_file_id": "..." } }
```

**PATCH /recruiter/applications/{id}/status**
```json
// Request
{ "status": "reviewing", "reason": "Looks promising" }

// Response
{ "success": true, "message": "Application status updated to reviewing", "data": { "id": "...", "status": "reviewing" } }
```

## Companies (`/companies`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/companies` | student | List (paginated, filterable) |
| GET | `/companies/{id}` | student | Detail + open postings |

### Request/Response Examples

**GET /companies?page=1&page_size=20&hiring_status=hiring**
```json
// Response
{ "success": true, "message": "Companies retrieved successfully", "data": { "companies": [{ "id": "...", "company_name": "Acme Corp", "hiring_status": "hiring", "tech_stack": ["Python", "React"], "location": "San Francisco" }], "total": 1, "page": 1, "page_size": 20 } }
```

**GET /companies/{id}**
```json
// Response
{ "success": true, "message": "Company details retrieved successfully", "data": { "id": "...", "company_name": "Acme Corp", "open_postings": [{ "id": "...", "title": "Software Engineer", "type": "job", "status": "open" }] } }
```

## Applications (`/applications`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/applications` | student | Create draft |
| POST | `/applications/{id}/resume` | student | Upload resume (multipart) |
| POST | `/applications/{id}/certificate` | student | Upload certificate (multipart) |
| POST | `/applications/{id}/submit` | student | Submit (requires resume) |
| GET | `/applications/{id}/resume` | student/recruiter | Download resume |
| GET | `/applications/{id}/certificate` | student/recruiter | Download certificate |
| DELETE | `/applications/{id}/resume` | student | Delete resume |
| DELETE | `/applications/{id}/certificate` | student | Delete certificate |
| POST | `/applications/{id}/verify` | student/recruiter | Start verification |
| GET | `/applications/{id}/verification` | student/recruiter | Get verification result |
| GET | `/applications/{id}/verification/stream` | student/recruiter | SSE progress stream |
| GET | `/verification/history/{app_id}` | student/recruiter | Past verification runs |

### Request/Response Examples

**POST /applications**
```json
// Request
{ "company_id": "cmp123", "posting_id": "post456", "github_project_link": "https://github.com/johndoe/project", "cover_letter": "I'm interested in this role..." }

// Response
{ "success": true, "message": "Application draft created successfully. Upload resume and submit.", "data": { "id": "...", "status": "draft", "github_project_link": "https://github.com/johndoe/project", "created_at": "..." } }
```

**POST /applications/{id}/resume** — `multipart/form-data` with `file` field
```json
// Response
{ "success": true, "message": "Resume uploaded successfully", "data": { "file_id": "...", "original_filename": "resume.pdf", "file_type": "resume", "file_size": 12345 } }
```

**POST /applications/{id}/certificate** — `multipart/form-data` with `file` field
```json
// Response
{ "success": true, "message": "Certificate uploaded successfully", "data": { "file_id": "...", "original_filename": "cert.pdf", "file_type": "certificate", "file_size": 6789 } }
```

**POST /applications/{id}/submit**
```json
// Response
{ "success": true, "message": "Application submitted successfully", "data": { "id": "...", "status": "submitted", "submitted_at": "..." } }
```

**GET /applications/{id}/resume** — Returns raw file binary (attachment download)
**GET /applications/{id}/certificate** — Returns raw file binary (attachment download)

**DELETE /applications/{id}/resume**
```json
// Response
{ "success": true, "message": "Resume deleted successfully", "data": {} }
```

**DELETE /applications/{id}/certificate**
```json
// Response
{ "success": true, "message": "Certificate deleted successfully", "data": {} }
```

**POST /applications/{id}/verify**
```json
// Response
{ "success": true, "message": "Verification completed", "data": { "id": "...", "status": "completed", "overall_score": 85, "verdict": "positive", "summary": "Credentials verified successfully" } }
```

**GET /applications/{id}/verification**
```json
// Response
{ "success": true, "message": "Verification result retrieved", "data": { "id": "...", "status": "completed", "overall_score": 85, "verdict": "positive" } }
```

**GET /applications/{id}/verification/stream** — Server-Sent Events
```
event: progress
data: {"type": "progress", "stage": "resume", "message": "Analyzing resume..."}

event: progress
data: {"type": "progress", "stage": "github", "message": "Verifying GitHub..."}

event: result
data: {"type": "result", "data": { "status": "completed", "overall_score": 85, "verdict": "positive" }}
```

**GET /verification/history/{app_id}**
```json
// Response
{ "success": true, "message": "Verification history retrieved", "data": { "history": [{ "id": "...", "version": 1, "status": "completed", "overall_score": 85 }], "total": 1 } }
```

## Admin (`/admin`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/admin/users` | any auth | List all users |
| GET | `/admin/students` | any auth | List students |
| GET | `/admin/recruiters` | any auth | List recruiters |
| PATCH | `/admin/user/status` | any auth | Activate/deactivate user |

### Request/Response Examples

**GET /admin/users?skip=0&limit=100**
```json
// Response
{ "success": true, "message": "All users retrieved", "data": { "students": [{ "id": "...", "full_name": "John Doe", "role": "student" }], "recruiters": [{ "id": "...", "company_name": "Acme Corp", "role": "recruiter" }], "total_students": 1, "total_recruiters": 1 } }
```

**GET /admin/students?skip=0&limit=100**
```json
// Response
{ "success": true, "message": "All students retrieved", "data": [{ "id": "...", "full_name": "John Doe", "role": "student" }] }
```

**GET /admin/recruiters?skip=0&limit=100**
```json
// Response
{ "success": true, "message": "All recruiters retrieved", "data": [{ "id": "...", "company_name": "Acme Corp", "role": "recruiter" }] }
```

**PATCH /admin/user/status?user_id=abc&role=student&is_active=true**
```json
// Response
{ "success": true, "message": "User activated successfully", "data": { "is_active": true } }
```

## Health

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/health` | — | Health check |

```json
// Response
{ "status": "healthy", "service": "VerifAI", "version": "1.0.0" }
```

## Response format

**Success:**
```json
{ "success": true, "message": "...", "data": {} }
```

**Error:**
```json
{ "success": false, "message": "...", "error_code": "CODE", "errors": [] }
```
