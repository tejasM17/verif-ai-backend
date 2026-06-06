import pytest
from unittest.mock import patch
from httpx import AsyncClient


class TestRecruiterEndpoints:
    @patch("app.services.auth.verify_firebase_token")
    @pytest.mark.asyncio
    async def test_get_recruiter_profile(self, mock_verify, client: AsyncClient):
        mock_verify.return_value = {
            "uid": "rec-profile-uid",
            "email": "recprofile@test.com",
        }
        reg_payload = {
            "firebase_token": "mock-token",
            "company_name": "Profile Corp",
            "recruiter_name": "Profile Rec",
        }
        reg_resp = await client.post("/auth/recruiter/register", json=reg_payload)
        access_token = reg_resp.json()["data"]["access_token"]

        resp = await client.get(
            "/recruiter/profile",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["recruiter_name"] == "Profile Rec"

    @patch("app.services.auth.verify_firebase_token")
    @pytest.mark.asyncio
    async def test_student_cannot_access_recruiter_route(
        self, mock_verify, client: AsyncClient
    ):
        mock_verify.return_value = {
            "uid": "student-access-rec-uid",
            "email": "stud@test.com",
        }
        reg_payload = {"firebase_token": "mock-token", "full_name": "Student User"}
        reg_resp = await client.post("/auth/student/register", json=reg_payload)
        access_token = reg_resp.json()["data"]["access_token"]

        resp = await client.get(
            "/recruiter/profile",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert resp.status_code == 403

    @patch("app.services.auth.verify_firebase_token")
    @pytest.mark.asyncio
    async def test_delete_recruiter_profile(self, mock_verify, client: AsyncClient):
        mock_verify.return_value = {
            "uid": "rec-delete-uid",
            "email": "recdelete@test.com",
        }
        reg_payload = {
            "firebase_token": "mock-token",
            "company_name": "Delete Corp",
            "recruiter_name": "Delete Rec",
        }
        reg_resp = await client.post("/auth/recruiter/register", json=reg_payload)
        access_token = reg_resp.json()["data"]["access_token"]

        resp = await client.delete(
            "/recruiter/profile",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert resp.status_code == 200
