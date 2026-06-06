import pytest
from unittest.mock import patch
from httpx import AsyncClient


class TestAuthEndpoints:
    @patch("app.auth.firebase.verify_firebase_token")
    @pytest.mark.asyncio
    async def test_health_check(self, mock_verify, client: AsyncClient):
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"

    @patch("app.auth.firebase.verify_firebase_token")
    @pytest.mark.asyncio
    async def test_student_register_success(self, mock_verify, client: AsyncClient):
        mock_verify.return_value = {
            "uid": "test-firebase-uid-123",
            "email": "student@test.com",
        }
        payload = {
            "firebase_token": "mock-firebase-token",
            "full_name": "Test Student",
            "college_name": "Test University",
            "branch": "Computer Science",
            "graduation_year": 2025,
        }
        resp = await client.post("/auth/student/register", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["user"]["role"] == "student"
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]

    @patch("app.auth.firebase.verify_firebase_token")
    @pytest.mark.asyncio
    async def test_recruiter_register_success(self, mock_verify, client: AsyncClient):
        mock_verify.return_value = {
            "uid": "test-firebase-uid-456",
            "email": "recruiter@test.com",
        }
        payload = {
            "firebase_token": "mock-firebase-token",
            "company_name": "Test Corp",
            "recruiter_name": "Test Recruiter",
            "designation": "HR Manager",
        }
        resp = await client.post("/auth/recruiter/register", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["user"]["role"] == "recruiter"

    @patch("app.auth.firebase.verify_firebase_token")
    @pytest.mark.asyncio
    async def test_duplicate_student_registration(self, mock_verify, client: AsyncClient):
        mock_verify.return_value = {
            "uid": "dup-firebase-uid",
            "email": "dup@test.com",
        }
        payload = {"firebase_token": "mock-token", "full_name": "Dup Student"}
        await client.post("/auth/student/register", json=payload)
        resp = await client.post("/auth/student/register", json=payload)
        assert resp.status_code == 409

    @patch("app.auth.firebase.verify_firebase_token")
    @pytest.mark.asyncio
    async def test_login_unregistered_user(self, mock_verify, client: AsyncClient):
        mock_verify.return_value = {
            "uid": "nonexistent-uid",
            "email": "nouser@test.com",
        }
        payload = {"firebase_token": "mock-token"}
        resp = await client.post("/auth/login", json=payload)
        assert resp.status_code == 404

    @patch("app.auth.firebase.verify_firebase_token")
    @pytest.mark.asyncio
    async def test_invalid_firebase_token(self, mock_verify, client: AsyncClient):
        from app.core.exceptions import UnauthorizedException
        mock_verify.side_effect = UnauthorizedException("Invalid Firebase token")
        payload = {"firebase_token": "bad-token", "full_name": "Test"}
        resp = await client.post("/auth/student/register", json=payload)
        assert resp.status_code == 401
