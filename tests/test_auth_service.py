import pytest
from unittest.mock import patch
from fastapi import HTTPException

from app.services.auth_service import AuthService


@pytest.fixture
def service(mock_firebase_auth):
    return AuthService()


class TestAuthService:
    def test_signup_returns_user(self, service, mock_firebase_auth):
        result = service.signup("a@b.com", "pass", role="recruiter")
        assert result["uid"] == "test_uid_123"
        assert result["email"] == "test@example.com"

    def test_signup_requires_role(self, service, mock_firebase_auth):
        with pytest.raises(HTTPException) as exc:
            service.signup("a@b.com", "pass")
        assert exc.value.status_code == 400
        assert "role" in str(exc.value.detail).lower()

    def test_signup_rejects_invalid_role(self, service, mock_firebase_auth):
        with pytest.raises(HTTPException) as exc:
            service.signup("a@b.com", "pass", role="admin")
        assert exc.value.status_code == 400
        assert "invalid role" in str(exc.value.detail).lower()

    def test_signup_raises_on_error(self, service, mock_firebase_auth):
        mock_firebase_auth.create_user.side_effect = Exception("fail")
        with pytest.raises(HTTPException) as exc:
            service.signup("a@b.com", "pass", role="student")
        assert exc.value.status_code == 400

    def test_get_current_user_success(self, service, mock_firebase_auth):
        result = service.get_current_user("valid_token")
        assert result["uid"] == "test_uid_123"
        assert result["email"] == "test@example.com"
        assert "role" in result

    def test_get_current_user_raises_on_invalid(self, service, mock_firebase_auth):
        mock_firebase_auth.verify_id_token.side_effect = Exception("bad")
        with pytest.raises(HTTPException) as exc:
            service.get_current_user("bad_token")
        assert exc.value.status_code == 401

    def test_get_current_user_returns_role(self, service, mock_firebase_auth):
        from app.repositories.user_repository import UserRepository

        with patch.object(
            UserRepository,
            "get_profile",
            return_value={
                "uid": "test_uid_123",
                "email": "test@example.com",
                "role": "recruiter",
            },
        ):
            result = service.get_current_user("valid_token")
            assert result["role"] == "recruiter"
