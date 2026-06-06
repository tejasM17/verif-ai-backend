# Postman Testing Guide

## Setup

1. Open Postman
2. Create a new Collection (e.g., "VerifAI")
3. Add the following environment variables:
   - `base_url` = `http://localhost:8000`
   - `firebase_token` = (get from Firebase client SDK)
   - `student_access_token` = (set from register/login response)
   - `student_refresh_token` = (set from register/login response)
   - `recruiter_access_token` = (set from register/login response)
   - `recruiter_refresh_token` = (set from register/login response)

---

## Health Check

**GET** `{{base_url}}/health`

Response:
```json
{
  "status": "healthy",
  "service": "VerifAI Backend",
  "version": "1.0.0"
}
```

---

## Authentication

### 1. Register Student

**POST** `{{base_url}}/auth/student/register`

**Headers:** `Content-Type: application/json`

**Body:**
```json
{
  "firebase_token": "FIREBASE_ID_TOKEN",
  "full_name": "John Doe",
  "phone": "+1234567890",
  "college_name": "MIT",
  "branch": "Computer Science",
  "graduation_year": 2025,
  "skills": "Python, JavaScript, AI",
  "resume_url": "https://resume.url"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Student registered successfully",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "user": {
      "id": "uuid-string",
      "email": "user@example.com",
      "full_name": "John Doe",
      "role": "student"
    }
  }
}
```

### 2. Register Recruiter

**POST** `{{base_url}}/auth/recruiter/register`

**Headers:** `Content-Type: application/json`

**Body:**
```json
{
  "firebase_token": "FIREBASE_ID_TOKEN",
  "company_name": "Google",
  "recruiter_name": "Jane Smith",
  "phone": "+1234567890",
  "company_website": "https://google.com",
  "company_logo": null,
  "designation": "Technical Recruiter"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Recruiter registered successfully",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "user": {
      "id": "uuid-string",
      "email": "recruiter@example.com",
      "full_name": "Jane Smith",
      "role": "recruiter"
    }
  }
}
```

### 3. Login

**POST** `{{base_url}}/auth/login`

**Headers:** `Content-Type: application/json`

**Body:**
```json
{
  "firebase_token": "FIREBASE_ID_TOKEN"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "user": {
      "id": "uuid-string",
      "email": "user@example.com",
      "full_name": "John Doe",
      "role": "student"
    }
  }
}
```

### 4. Refresh Token

**POST** `{{base_url}}/auth/refresh`

**Headers:** `Content-Type: application/json`

**Body:**
```json
{
  "refresh_token": "REFRESH_TOKEN"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Token refreshed successfully",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer"
  }
}
```

### 5. Logout

**POST** `{{base_url}}/auth/logout`

**Headers:**
- `Content-Type: application/json`
- `Authorization: Bearer ACCESS_TOKEN`

**Body:**
```json
{
  "refresh_token": "REFRESH_TOKEN"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Logged out successfully",
  "data": {}
}
```

---

## Student Endpoints

All student endpoints require `Authorization: Bearer STUDENT_ACCESS_TOKEN` header.

### 6. Get Student Profile

**GET** `{{base_url}}/student/profile`

**Response (200):**
```json
{
  "success": true,
  "message": "Student profile retrieved",
  "data": {
    "id": "uuid-string",
    "firebase_uid": "firebase-uid",
    "full_name": "John Doe",
    "email": "user@example.com",
    "phone": "+1234567890",
    "college_name": "MIT",
    "branch": "Computer Science",
    "graduation_year": 2025,
    "skills": "Python, JavaScript, AI",
    "resume_url": "https://resume.url",
    "role": "student",
    "is_active": true,
    "created_at": "2025-01-01T00:00:00",
    "updated_at": "2025-01-01T00:00:00"
  }
}
```

### 7. Update Student Profile

**PUT** `{{base_url}}/student/profile`

**Headers:**
- `Content-Type: application/json`
- `Authorization: Bearer STUDENT_ACCESS_TOKEN`

**Body (all fields optional):**
```json
{
  "full_name": "Updated Name",
  "phone": "+9876543210",
  "college_name": "Stanford",
  "branch": "Data Science",
  "graduation_year": 2026,
  "skills": "Python, ML, Cloud",
  "resume_url": "https://new-resume.url"
}
```

### 8. Delete Student Profile

**DELETE** `{{base_url}}/student/profile`

**Headers:** `Authorization: Bearer STUDENT_ACCESS_TOKEN`

---

## Recruiter Endpoints

All recruiter endpoints require `Authorization: Bearer RECRUITER_ACCESS_TOKEN` header.

### 9. Get Recruiter Profile

**GET** `{{base_url}}/recruiter/profile`

**Response (200):**
```json
{
  "success": true,
  "message": "Recruiter profile retrieved",
  "data": {
    "id": "uuid-string",
    "firebase_uid": "firebase-uid",
    "company_name": "Google",
    "recruiter_name": "Jane Smith",
    "email": "recruiter@example.com",
    "phone": "+1234567890",
    "company_website": "https://google.com",
    "designation": "Technical Recruiter",
    "role": "recruiter",
    "is_active": true,
    "created_at": "2025-01-01T00:00:00",
    "updated_at": "2025-01-01T00:00:00"
  }
}
```

### 10. Update Recruiter Profile

**PUT** `{{base_url}}/recruiter/profile`

**Headers:**
- `Content-Type: application/json`
- `Authorization: Bearer RECRUITER_ACCESS_TOKEN`

**Body (all fields optional):**
```json
{
  "company_name": "New Corp",
  "recruiter_name": "New Name",
  "phone": "+9876543210",
  "company_website": "https://new-website.com",
  "designation": "Senior HR"
}
```

### 11. Delete Recruiter Profile

**DELETE** `{{base_url}}/recruiter/profile`

**Headers:** `Authorization: Bearer RECRUITER_ACCESS_TOKEN`

---

## Admin Endpoints

All admin endpoints require `Authorization: Bearer ACCESS_TOKEN` header.

### 12. Get All Users

**GET** `{{base_url}}/admin/users?skip=0&limit=100`

### 13. Get All Students

**GET** `{{base_url}}/admin/students?skip=0&limit=100`

### 14. Get All Recruiters

**GET** `{{base_url}}/admin/recruiters?skip=0&limit=100`

### 15. Update User Status

**PATCH** `{{base_url}}/admin/user/status?user_id=UUID&role=student&is_active=false`

---

## Authorization Tests

| Test | Action | Expected |
|------|--------|----------|
| Student accessing student route | `GET /student/profile` with student token | 200 |
| Recruiter accessing recruiter route | `GET /recruiter/profile` with recruiter token | 200 |
| Student accessing recruiter route | `GET /recruiter/profile` with student token | 403 |
| Recruiter accessing student route | `GET /student/profile` with recruiter token | 403 |
| Invalid token | `GET /student/profile` with `Bearer invalid` | 401 |
| No token | `GET /student/profile` | 401 |

---

## Response Format

**Success:**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {}
}
```

**Error:**
```json
{
  "success": false,
  "message": "Error message",
  "errors": []
}
```

## HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 409 | Conflict |
| 422 | Validation Error |
| 429 | Rate Limit Exceeded |
| 500 | Internal Server Error |
