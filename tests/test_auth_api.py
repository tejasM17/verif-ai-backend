import pytest
from unittest.mock import patch


class TestAuthAPI:
    def test_health_check(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.json() == {"message": "VerifAI Backend Running"}

    def test_signup_success(self, client, mock_firebase_auth):
        resp = client.post(
            "/signup",
            json={
                "email": "new@example.com",
                "password": "secret123",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["uid"] == "test_uid_123"
        assert data["email"] == "test@example.com"
        mock_firebase_auth.create_user.assert_called_once_with(
            email="new@example.com", password="secret123"
        )

    def test_signup_failure(self, client, mock_firebase_auth):
        mock_firebase_auth.create_user.side_effect = Exception("Email already exists")
        resp = client.post(
            "/signup",
            json={
                "email": "existing@example.com",
                "password": "secret123",
            },
        )
        assert resp.status_code == 400
        assert "Email already exists" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_success(self, client, mock_firebase_auth):
        mock_response = {
            "idToken": "mock_token",
            "email": "test@example.com",
            "localId": "mock_local_id",
        }
        with patch(
            "app.repositories.firebase_repository.FirebaseRepository.sign_in_with_password",
            return_value=mock_response,
        ):
            resp = client.post(
                "/login",
                json={
                    "email": "test@example.com",
                    "password": "secret123",
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["idToken"] == "mock_token"
            assert data["email"] == "test@example.com"

    def test_me_unauthorized(self, client):
        resp = client.get("/me")
        assert resp.status_code == 401

    def test_me_success(self, client):
        resp = client.get("/me", headers={"Authorization": "Bearer valid_token"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["uid"] == "test_uid_123"
        assert data["email"] == "test@example.com"
        assert "role" in data

    def test_me_invalid_token(self, client):
        with patch("app.api.dependencies.verify_token", return_value=None):
            resp = client.get("/me", headers={"Authorization": "Bearer bad_token"})
        assert resp.status_code == 401

    def test_me_returns_role(self, client, mock_firebase_auth):
        from app.repositories.user_repository import UserRepository

        with patch.object(
            UserRepository,
            "get_profile",
            return_value={
                "uid": "test_uid_123",
                "email": "test@example.com",
                "role": "student",
            },
        ):
            resp = client.get("/me", headers={"Authorization": "Bearer valid_token"})
            assert resp.status_code == 200
            data = resp.json()
            assert data["role"] == "student"
