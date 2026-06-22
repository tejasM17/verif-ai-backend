from unittest.mock import patch


class TestProfileAPI:
    def test_profile_me_unauthorized(self, client):
        resp = client.get("/profile/me")
        assert resp.status_code == 401

    def test_profile_me_success(self, client, mock_firebase_auth):
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
            resp = client.get(
                "/profile/me", headers={"Authorization": "Bearer valid_token"}
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["uid"] == "test_uid_123"
            assert data["role"] == "student"

    def test_onboarding_success(self, client, mock_firebase_auth):
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
            resp = client.post(
                "/profile/onboarding",
                json={"role": "student"},
                headers={"Authorization": "Bearer valid_token"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["role"] == "student"

    def test_student_route_success(self, client, mock_firebase_auth):
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
            resp = client.get(
                "/profile/student",
                headers={"Authorization": "Bearer valid_token"},
            )
            assert resp.status_code == 200

    def test_student_route_forbidden_for_recruiter(self, client, mock_firebase_auth):
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
            resp = client.get(
                "/profile/student",
                headers={"Authorization": "Bearer valid_token"},
            )
            assert resp.status_code == 403

    def test_recruiter_route_success(self, client, mock_firebase_auth):
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
            resp = client.get(
                "/profile/recruiter",
                headers={"Authorization": "Bearer valid_token"},
            )
            assert resp.status_code == 200

    def test_recruiter_route_forbidden_for_student(self, client, mock_firebase_auth):
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
            resp = client.get(
                "/profile/recruiter",
                headers={"Authorization": "Bearer valid_token"},
            )
            assert resp.status_code == 403

    def test_onboarding_unauthorized(self, client):
        resp = client.post("/profile/onboarding", json={"role": "student"})
        assert resp.status_code == 401
