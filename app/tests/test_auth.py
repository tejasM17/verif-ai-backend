import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient

from app.services.auth import AuthService


def _fake_firebase_token(uid: str, email: str) -> dict:
    return {"uid": uid, "email": email}


class TestAuthEndpoints:
    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"

    @patch("app.services.auth.verify_firebase_token")
    @pytest.mark.asyncio
    async def test_student_register_with_firebase(self, mock_verify, client: AsyncClient, auth_repo):
        mock_verify.return_value = _fake_firebase_token("fb-uid-001", "student1@test.com")
        payload = {
            "firebase_token": "mock-fb-token",
            "full_name": "Test Student",
            "college_name": "Test University",
            "branch": "Computer Science",
            "graduation_year": 2025,
        }
        resp = await client.post("/auth/register/student", json=payload)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["user"]["role"] == "student"
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]

    @pytest.mark.asyncio
    async def test_student_register_with_email_password(self, client: AsyncClient, auth_repo):
        payload = {
            "email": "student2@test.com",
            "password": "securepass123",
            "full_name": "Email Student",
        }
        resp = await client.post("/auth/register/student", json=payload)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["user"]["role"] == "student"
        assert data["data"]["user"]["email"] == "student2@test.com"

    @pytest.mark.asyncio
    async def test_student_register_requires_email_or_firebase(self, client: AsyncClient):
        payload = {"full_name": "No Email Student"}
        resp = await client.post("/auth/register/student", json=payload)
        assert resp.status_code == 422

    @patch("app.services.auth.verify_firebase_token")
    @pytest.mark.asyncio
    async def test_recruiter_register_with_firebase(self, mock_verify, client: AsyncClient, auth_repo):
        mock_verify.return_value = _fake_firebase_token("fb-uid-002", "recruiter1@test.com")
        payload = {
            "firebase_token": "mock-fb-token",
            "company_name": "Test Corp",
            "recruiter_name": "Test Recruiter",
            "designation": "HR Manager",
        }
        resp = await client.post("/auth/register/recruiter", json=payload)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["user"]["role"] == "recruiter"

    @pytest.mark.asyncio
    async def test_recruiter_register_with_email_password(self, client: AsyncClient, auth_repo):
        payload = {
            "email": "recruiter2@test.com",
            "password": "securepass456",
            "company_name": "Email Corp",
            "recruiter_name": "Email Recruiter",
        }
        resp = await client.post("/auth/register/recruiter", json=payload)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["user"]["role"] == "recruiter"

    @patch("app.services.auth.verify_firebase_token")
    @pytest.mark.asyncio
    async def test_duplicate_email_registration(self, mock_verify, client: AsyncClient, auth_repo):
        await auth_repo.create_user(email="dup@test.com", firebase_uid="dup-uid", role="student")

        mock_verify.return_value = _fake_firebase_token("dup-uid", "dup@test.com")
        payload = {"firebase_token": "mock-token", "full_name": "Dup Student"}
        resp = await client.post("/auth/register/student", json=payload)
        assert resp.status_code == 409
        data = resp.json()
        assert data["error_code"] == "USER_ALREADY_REGISTERED"

    @patch("app.services.auth.verify_firebase_token")
    @pytest.mark.asyncio
    async def test_login_with_firebase(self, mock_verify, client: AsyncClient, auth_repo):
        mock_verify.return_value = _fake_firebase_token("login-fb-uid", "login@test.com")
        reg_payload = {"firebase_token": "mock-token", "full_name": "Login User"}
        await client.post("/auth/register/student", json=reg_payload)

        login_payload = {"firebase_token": "mock-token"}
        resp = await client.post("/auth/login", json=login_payload)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["success"] is True
        assert "access_token" in data["data"]

    @pytest.mark.asyncio
    async def test_login_with_email_password(self, client: AsyncClient, auth_repo):
        reg_payload = {"email": "login@test.com", "password": "pass123", "full_name": "Login User"}
        await client.post("/auth/register/student", json=reg_payload)

        login_payload = {"email": "login@test.com", "password": "pass123"}
        resp = await client.post("/auth/login", json=login_payload)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["success"] is True
        assert "access_token" in data["data"]

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, auth_repo):
        reg_payload = {"email": "wrongpw@test.com", "password": "correctpass", "full_name": "PW User"}
        await client.post("/auth/register/student", json=reg_payload)

        login_payload = {"email": "wrongpw@test.com", "password": "wrongpass"}
        resp = await client.post("/auth/login", json=login_payload)
        assert resp.status_code == 401
        data = resp.json()
        assert data["error_code"] == "INVALID_CREDENTIALS"

    @pytest.mark.asyncio
    async def test_login_unregistered_user(self, client: AsyncClient):
        payload = {"email": "nobody@test.com", "password": "pass123"}
        resp = await client.post("/auth/login", json=payload)
        assert resp.status_code == 404
        data = resp.json()
        assert data["error_code"] == "USER_NOT_REGISTERED"

    @patch("app.services.auth.verify_firebase_token")
    @pytest.mark.asyncio
    async def test_get_current_user(self, mock_verify, client: AsyncClient, auth_repo):
        mock_verify.return_value = _fake_firebase_token("me-uid", "me@test.com")
        reg_payload = {"firebase_token": "mock-token", "full_name": "Me User"}
        reg_resp = await client.post("/auth/register/student", json=reg_payload)
        access_token = reg_resp.json()["data"]["access_token"]

        resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {access_token}"})
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["email"] == "me@test.com"

    @pytest.mark.asyncio
    async def test_get_current_user_no_token(self, client: AsyncClient):
        resp = await client.get("/auth/me")
        assert resp.status_code == 401
        assert resp.json()["error_code"] == "NO_CREDENTIALS"

    @patch("app.services.auth.verify_firebase_token")
    @pytest.mark.asyncio
    async def test_auth_me_with_cookie(self, mock_verify, client: AsyncClient, auth_repo):
        mock_verify.return_value = _fake_firebase_token("cookie-uid", "cookie@test.com")
        reg_payload = {"firebase_token": "mock-token", "full_name": "Cookie User"}
        reg_resp = await client.post("/auth/register/student", json=reg_payload)
        tokens = reg_resp.json()["data"]
        cookies = reg_resp.cookies

        resp = await client.get(
            "/auth/me",
            cookies={"access_token": tokens["access_token"]},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["data"]["email"] == "cookie@test.com"

    @patch("app.services.auth.verify_firebase_token")
    @pytest.mark.asyncio
    async def test_refresh_token_rotation(self, mock_verify, client: AsyncClient, auth_repo):
        mock_verify.return_value = _fake_firebase_token("refresh-uid", "refresh@test.com")
        reg_payload = {"firebase_token": "mock-token", "full_name": "Refresh User"}
        reg_resp = await client.post("/auth/register/student", json=reg_payload)
        old_refresh = reg_resp.json()["data"]["refresh_token"]
        old_access = reg_resp.json()["data"]["access_token"]

        refresh_resp = await client.post("/auth/refresh", json={"refresh_token": old_refresh})
        assert refresh_resp.status_code == 200, refresh_resp.text
        new_tokens = refresh_resp.json()["data"]
        assert new_tokens["access_token"] != old_access
        assert new_tokens["refresh_token"] != old_refresh

        reused_resp = await client.post("/auth/refresh", json={"refresh_token": old_refresh})
        assert reused_resp.status_code == 401
        assert reused_resp.json()["error_code"] == "TOKEN_REUSED"

    @patch("app.services.auth.verify_firebase_token")
    @pytest.mark.asyncio
    async def test_protected_endpoint_with_cookie(self, mock_verify, client: AsyncClient, auth_repo):
        mock_verify.return_value = _fake_firebase_token("prot-cookie-uid", "prot@test.com")
        reg_payload = {"firebase_token": "mock-token", "full_name": "Protected Cookie"}
        reg_resp = await client.post("/auth/register/student", json=reg_payload)
        access_token = reg_resp.json()["data"]["access_token"]

        resp = await client.get(
            "/student/profile",
            cookies={"access_token": access_token},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["data"]["full_name"] == "Protected Cookie"

    @patch("app.services.auth.verify_firebase_token")
    @pytest.mark.asyncio
    async def test_logout(self, mock_verify, client: AsyncClient, auth_repo):
        mock_verify.return_value = _fake_firebase_token("logout-uid", "logout@test.com")
        reg_payload = {"firebase_token": "mock-token", "full_name": "Logout User"}
        reg_resp = await client.post("/auth/register/student", json=reg_payload)
        tokens = reg_resp.json()["data"]

        logout_resp = await client.post(
            "/auth/logout",
            json={"refresh_token": tokens["refresh_token"]},
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert logout_resp.status_code == 200

    @pytest.mark.asyncio
    async def test_role_based_access_student(self, client: AsyncClient, auth_repo):
        reg_payload = {"email": "studentrole@test.com", "password": "pass123", "full_name": "Role Student"}
        reg_resp = await client.post("/auth/register/student", json=reg_payload)
        token = reg_resp.json()["data"]["access_token"]

        resp = await client.get("/student/profile", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200, resp.text

    @pytest.mark.asyncio
    async def test_role_based_access_recruiter_blocked_from_student(self, client: AsyncClient, auth_repo):
        reg_payload = {"email": "recruiterrole@test.com", "password": "pass123", "company_name": "TestCorp", "recruiter_name": "Test Recruiter"}
        reg_resp = await client.post("/auth/register/recruiter", json=reg_payload)
        token = reg_resp.json()["data"]["access_token"]

        resp = await client.get("/student/profile", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403
        assert resp.json()["error_code"] == "ROLE_MISMATCH"

    @pytest.mark.asyncio
    async def test_student_blocked_from_recruiter(self, client: AsyncClient, auth_repo):
        reg_payload = {"email": "studentblock@test.com", "password": "pass123", "full_name": "Block Student"}
        reg_resp = await client.post("/auth/register/student", json=reg_payload)
        token = reg_resp.json()["data"]["access_token"]

        resp = await client.get("/recruiter/profile", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403
        assert resp.json()["error_code"] == "ROLE_MISMATCH"
