from fastapi import HTTPException
from app.domain.enums.role import UserRole
from app.repositories.firebase_repository import FirebaseRepository
from app.services.user_service import UserService

repo = FirebaseRepository()
user_service = UserService()


class AuthService:
    def signup(self, email: str, password: str, role: str | None = None):
        try:
            user = repo.create_user(email, password)
            # Require a valid role at signup so accounts never end up role-less.
            # The frontend must always send 'student' or 'recruiter'.
            if not role:
                raise ValueError(
                    "role is required at signup (must be 'student' or 'recruiter')"
                )
            try:
                role_enum = UserRole(role)
            except ValueError as e:
                raise ValueError(
                    f"invalid role '{role}': must be 'student' or 'recruiter'"
                ) from e
            user_service.get_or_create_profile(
                uid=user.uid, email=email, display_name=None, photo_url=None
            )
            user_service.set_role(user.uid, role_enum)
            return {"uid": user.uid, "email": user.email}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    async def login(self, email: str, password: str):
        data = await repo.sign_in_with_password(email, password)
        if "idToken" not in data:
            raise HTTPException(
                status_code=401,
                detail=data.get("error", {}).get("message", "Login failed"),
            )
        uid = data.get("localId", "")
        profile = user_service.get_or_create_profile(
            uid=uid,
            email=data.get("email", ""),
        )
        return {
            "idToken": data["idToken"],
            "email": data["email"],
            "localId": uid,
            "role": profile.get("role"),
        }

    def _social_login(self, id_token: str):
        decoded = repo.verify_token(id_token)
        uid = decoded["uid"]
        email = decoded.get("email", "")
        display_name = decoded.get("name", "")
        photo_url = decoded.get("picture", "")
        profile = user_service.get_or_create_profile(
            uid=uid,
            email=email,
            display_name=display_name,
            photo_url=photo_url,
        )
        if not profile.get("role"):
            profile = user_service.set_role(uid, UserRole.student)
        return {
            "idToken": id_token,
            "email": email,
            "localId": uid,
            "displayName": display_name,
            "photoUrl": photo_url,
            "role": profile.get("role"),
        }

    def google_login(self, id_token: str):
        try:
            return self._social_login(id_token)
        except Exception as e:
            raise HTTPException(status_code=401, detail=str(e))

    def github_login(self, id_token: str):
        try:
            return self._social_login(id_token)
        except Exception as e:
            raise HTTPException(status_code=401, detail=str(e))

    def get_current_user(self, token: str):
        try:
            decoded = repo.verify_token(token)
            profile = user_service.get_or_create_profile(
                uid=decoded["uid"],
                email=decoded.get("email", ""),
                display_name=decoded.get("name"),
                photo_url=decoded.get("picture"),
            )
            return {
                "uid": decoded["uid"],
                "email": decoded.get("email", ""),
                "displayName": decoded.get("name"),
                "photoUrl": decoded.get("picture"),
                "role": profile.get("role"),
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=401, detail=str(e))
