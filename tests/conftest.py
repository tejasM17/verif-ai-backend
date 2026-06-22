import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.core.config import settings
from fastapi import FastAPI


@pytest.fixture(autouse=True)
def mock_firebase_deps():
    with (
        patch("app.repositories.firebase_repository.auth") as mock_repo_auth,
        patch("app.core.config.firebase_admin") as mock_firebase_admin,
        patch("app.repositories.user_repository.db") as mock_db,
        patch("app.core.security.verify_token") as mock_verify_token,
    ):
        mock_firebase_admin._apps = {}
        mock_firebase_admin.initialize_app.return_value = None

        mock_ref = MagicMock()
        mock_db.reference.return_value = mock_ref
        mock_ref.get.return_value = None

        mock_repo_auth.create_user.return_value = MagicMock(
            uid="test_uid_123", email="test@example.com"
        )
        mock_repo_auth.verify_id_token.return_value = {
            "uid": "test_uid_123",
            "email": "test@example.com",
        }

        mock_verify_token.return_value = {
            "uid": "test_uid_123",
            "email": "test@example.com",
        }

        yield mock_repo_auth


@pytest.fixture
def app():
    from app.api.v1.auth import router as auth_router
    from app.api.v1.profile import router as profile_router

    application = FastAPI(title=settings.APP_TITLE)
    application.include_router(auth_router)
    application.include_router(profile_router)
    return application


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def mock_firebase_auth(mock_firebase_deps):
    return mock_firebase_deps
