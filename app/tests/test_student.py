import pytest
from unittest.mock import patch
from httpx import AsyncClient


class TestStudentEndpoints:
    @patch("app.services.auth.verify_firebase_token")
    @pytest.mark.asyncio
    async def test_get_student_profile(self, mock_verify, client: AsyncClient):
        mock_verify.return_value = {
            "uid": "student-profile-uid",
            "email": "profile@test.com",
        }
        reg_payload = {"firebase_token": "mock-token", "full_name": "Profile Test"}
        reg_resp = await client.post("/auth/register/student", json=reg_payload)
        tokens = reg_resp.json()["data"]
        access_token = tokens["access_token"]

        resp = await client.get(
            "/student/profile",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["full_name"] == "Profile Test"

    @patch("app.services.auth.verify_firebase_token")
    @pytest.mark.asyncio
    async def test_recruiter_cannot_access_student_route(
        self, mock_verify, client: AsyncClient
    ):
        mock_verify.return_value = {
            "uid": "recruiter-access-uid",
            "email": "rec@test.com",
        }
        reg_payload = {
            "firebase_token": "mock-token",
            "company_name": "Corp",
            "recruiter_name": "Rec",
        }
        reg_resp = await client.post("/auth/register/recruiter", json=reg_payload)
        access_token = reg_resp.json()["data"]["access_token"]

        resp = await client.get(
            "/student/profile",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert resp.status_code == 403
