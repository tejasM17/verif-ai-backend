import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.core.config import settings
from app.api.v1.auth import router
from fastapi import FastAPI


@pytest.fixture(autouse=True)
def mock_firebase_admin():
    with (
        patch("app.repositories.firebase_repository.auth") as mock_auth,
        patch("app.core.config.firebase_admin") as mock_firebase_admin,
    ):
        mock_firebase_admin._apps = {}
        mock_firebase_admin.initialize_app.return_value = None
        yield mock_auth


@pytest.fixture
def app():
    application = FastAPI(title=settings.APP_TITLE)
    application.include_router(router)
    return application


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def mock_firebase_auth(mock_firebase_admin):
    mock_firebase_admin.create_user.return_value = MagicMock(
        uid="test_uid_123", email="test@example.com"
    )
    mock_firebase_admin.verify_id_token.return_value = {
        "uid": "test_uid_123",
        "email": "test@example.com",
    }
    return mock_firebase_admin
