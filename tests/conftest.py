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

        # Simulate Firebase RTDB by holding writes in an in-memory dict and
        # returning them on subsequent reads. This lets the signup flow
        # actually persist a profile so set_role's `get_profile` check passes.
        rtdb_store: dict[str, dict] = {}

        def _ref(path):
            # path is like "users/<uid>"
            ref_mock = MagicMock()
            uid = path.split("/")[-1]

            def _get(*_args, **_kwargs):
                return rtdb_store.get(uid)

            def _set(value, *_args, **_kwargs):
                rtdb_store[uid] = dict(value) if value is not None else None

            def _update(value, *_args, **_kwargs):
                existing = rtdb_store.get(uid) or {}
                existing.update(value)
                rtdb_store[uid] = existing

            def _delete(*_args, **_kwargs):
                rtdb_store.pop(uid, None)

            ref_mock.get.side_effect = _get
            ref_mock.set.side_effect = _set
            ref_mock.update.side_effect = _update
            ref_mock.delete.side_effect = _delete
            return ref_mock

        mock_db.reference.side_effect = _ref

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
