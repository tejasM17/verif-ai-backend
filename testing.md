# Postman Step-by-Step Test Plan

## Postman Setup

### Environment Variables

| Variable | Example |
|----------|---------|
| `base_url` | `http://localhost:8000` |
| `firebase_token` | (set dynamically from frontend or Firebase SDK) |
| `student_access_token` | (from register/login response) |
| `student_refresh_token` | (from register/login response) |
| `recruiter_access_token` | (from register/login response) |
| `recruiter_refresh_token` | (from register/login response) |

### How to obtain a Firebase ID token for testing

Use the browser app to sign in, then in DevTools Console run:

```javascript
const token = await firebase.auth().currentUser.getIdToken();
console.log(token);
```

Copy the token into Postman variable `firebase_token`.

---

## 1. Health Check

**GET** `{{base_url}}/health`

Expect: `200` and service metadata.

```json
{
  "status": "healthy",
  "service": "VerifAI Backend",
  "version": "1.0.0"
}
```

---

## 2. Student Registration

**POST** `{{base_url}}/auth/student/register`

**Headers:** `Content-Type: application/json`

**Body:**
```json
{
  "firebase_token": "{{firebase_token}}",
  "full_name": "John Doe",
  "phone": "+1234567890",
  "college_name": "MIT",
  "branch": "Computer Science",
  "graduation_year": 2025,
  "skills": "Python, JavaScript, AI",
  "resume_url": "https://resume.url"
}
```

Expect: `200` with `access_token`, `refresh_token`, and `role: student`.

**Postman Tests tab:**
```javascript
pm.test("Status 200", () => pm.response.to.have.status(200));
pm.test("Has access_token", () => pm.expect(pm.response.json().data.access_token).to.not.be.empty);
pm.test("Has refresh_token", () => pm.expect(pm.response.json().data.refresh_token).to.not.be.empty);
pm.test("Role is student", () => pm.expect(pm.response.json().data.user.role).to.eql("student"));

var json = pm.response.json();
pm.environment.set("student_access_token", json.data.access_token);
pm.environment.set("student_refresh_token", json.data.refresh_token);
```

---

## 3. Recruiter Registration

**POST** `{{base_url}}/auth/recruiter/register`

**Body:**
```json
{
  "firebase_token": "{{firebase_token}}",
  "company_name": "Google",
  "recruiter_name": "Jane Smith",
  "phone": "+1234567890",
  "company_website": "https://google.com",
  "designation": "Technical Recruiter"
}
```

Expect: `200` with `role: recruiter`.

**Postman Tests tab:**
```javascript
pm.test("Status 200", () => pm.response.to.have.status(200));
pm.test("Role is recruiter", () => pm.expect(pm.response.json().data.user.role).to.eql("recruiter"));

var json = pm.response.json();
pm.environment.set("recruiter_access_token", json.data.access_token);
pm.environment.set("recruiter_refresh_token", json.data.refresh_token);
```

---

## 4. Login (all roles)

**POST** `{{base_url}}/auth/login`

**Body:**
```json
{
  "firebase_token": "{{firebase_token}}"
}
```

Expect: `200` and role-specific user object.

If you get `error_code: "TOKEN_USED_TOO_EARLY"`:
Wait 2 seconds, fetch a fresh Firebase token, and retry once. If it still fails, verify server NTP sync.

---

## 5. Get Current User (Session Restore)

**GET** `{{base_url}}/auth/me`

**Headers:** `Authorization: Bearer {{student_access_token}}`

Expect: `200` with `role`, `email`, `full_name`, `id`.

This is the endpoint the frontend should call on page reload to restore the session. It works for both students and recruiters.

**Postman Tests tab:**
```javascript
pm.test("Status 200", () => pm.response.to.have.status(200));
pm.test("Has role", () => pm.expect(pm.response.json().data.role).to.not.be.empty);
pm.test("Has email", () => pm.expect(pm.response.json().data.email).to.not.be.empty);
```

---

## 6. Get Student Profile

**GET** `{{base_url}}/student/profile`

**Headers:** `Authorization: Bearer {{student_access_token}}`

Expect: `200` and profile payload.

---

## 7. Update Student Profile

**PUT** `{{base_url}}/student/profile`

**Headers:**
- `Content-Type: application/json`
- `Authorization: Bearer {{student_access_token}}`

**Body:**
```json
{
  "full_name": "Updated Name",
  "college_name": "Stanford",
  "branch": "Data Science"
}
```

Expect: `200` and updated data.

---

## 8. Upload Profile Photo (multipart)

**POST** `{{base_url}}/student/profile/photo`

**Headers:** `Authorization: Bearer {{student_access_token}}`

**Body:** form-data → key `photo` (type File) → choose a JPG/PNG/WebP under 5MB.

Expect: `200` and `photo_url`.

---

## 9. Fetch Profile Photo

**GET** `{{base_url}}/student/profile/photo`

**Headers:** `Authorization: Bearer {{student_access_token}}`

Expect: `200` with image content type.

---

## 10. Refresh Token

**POST** `{{base_url}}/auth/refresh`

**Body:**
```json
{
  "refresh_token": "{{student_refresh_token}}"
}
```

Expect: `200` with a new access token. Update the environment variable.

**Postman Tests tab:**
```javascript
var json = pm.response.json();
pm.environment.set("student_access_token", json.data.access_token);
pm.environment.set("student_refresh_token", json.data.refresh_token);
```

---

## 11. Logout

**POST** `{{base_url}}/auth/logout`

**Headers:** `Authorization: Bearer {{student_access_token}}`

**Body:**
```json
{
  "refresh_token": "{{student_refresh_token}}"
}
```

Expect: `200` and token invalidation.

**Verification:** Attempt `GET /student/profile` with the old access token and expect `401`.

---

## Response Contract

### Success
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {}
}
```

### Error
```json
{
  "success": false,
  "message": "Error description",
  "error_code": "ERROR_CODE_STRING",
  "errors": []
}
```

---

## Error Codes Reference

| error_code | Status | Source | Description |
|-----------|--------|--------|-------------|
| `TOKEN_USED_TOO_EARLY` | 401 | Firebase | Server clock out of sync — retry after fresh token |
| `FIREBASE_PROJECT_MISMATCH` | 401 | Firebase | Token `aud` differs from project ID |
| `INVALID_FIREBASE_TOKEN` | 401 | Firebase | Malformed or wrong-project token |
| `TOKEN_EXPIRED` | 401 | Firebase | Firebase token past `exp` |
| `TOKEN_REVOKED` | 401 | App | Token revoked by explicit logout or admin action |
| `TOKEN_REUSED` | 401 | App | Refresh token reused after rotation — frontend should silently re-authenticate |
| `TOKEN_INVALID` | 401 | App | Generic invalid token (malformed, wrong secret, wrong format) |
| `USER_NOT_REGISTERED` | 404 | App | Valid token but no user document found |
| `USER_ALREADY_REGISTERED` | 409 | App | Duplicate registration attempt |
| `ACCOUNT_DISABLED` | 401 | App | Account disabled by admin |
| `NO_CREDENTIALS` | 401 | App | No Authorization header |
| `INVALID_ACCESS_TOKEN` | 401 | App JWT | Access token malformed or wrong secret |
| `ACCESS_TOKEN_EXPIRED` | 401 | App JWT | Access token past `exp` |
| `INVALID_REFRESH_TOKEN` | 401 | App JWT | Refresh token malformed or wrong secret |
| `REFRESH_TOKEN_EXPIRED` | 401 | App JWT | Refresh token past `exp` |
| `INVALID_TOKEN_TYPE` | 401 | App JWT | Token `type` claim is not `access`/`refresh` |
| `ROLE_MISMATCH` | 403 | App | Wrong role for endpoint |
| `USER_NOT_FOUND` | 401 | App | User document missing or inactive |

---

## Authorization Test Matrix

| Test | Action | Expected Status |
|------|--------|-----------------|
| Valid student token | `GET /student/profile` | 200 |
| Valid recruiter token | `GET /recruiter/profile` | 200 |
| Student on recruiter route | `GET /recruiter/profile` with student token | 403 (`ROLE_MISMATCH`) |
| Recruiter on student route | `GET /student/profile` with recruiter token | 403 (`ROLE_MISMATCH`) |
| Invalid access token | `GET /student/profile` with `Bearer invalid` | 401 (`INVALID_ACCESS_TOKEN`) |
| Expired access token | `GET /student/profile` with expired token | 401 (`ACCESS_TOKEN_EXPIRED`) |
| No token | `GET /student/profile` | 401 (`NO_CREDENTIALS`) |
| Expired refresh token | `POST /auth/refresh` with expired refresh token | 401 (`REFRESH_TOKEN_EXPIRED`) |
| Revoked refresh token | `POST /auth/refresh` after logout | 401 (`TOKEN_REVOKED`) |
| Reused refresh token | `POST /auth/refresh` with already-rotated token | 401 (`TOKEN_REUSED`) |
| /auth/me valid token | `GET /auth/me` with valid access token | 200 |
| /auth/me expired token | `GET /auth/me` with expired access token | 401 (`ACCESS_TOKEN_EXPIRED`) |
| /auth/me no token | `GET /auth/me` without header | 401 (`NO_CREDENTIALS`) |

---

## HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 409 | Conflict |
| 422 | Validation Error |
| 429 | Rate Limit Exceeded |
| 500 | Internal Server Error |
