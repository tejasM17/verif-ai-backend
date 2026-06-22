from fastapi import HTTPException, status

from app.domain.entities.user import UserEntity
from app.domain.enums.role import UserRole
from app.repositories.user_repository import UserRepository

repo = UserRepository()


class UserService:
    def get_or_create_profile(
        self,
        uid: str,
        email: str,
        display_name: str | None = None,
        photo_url: str | None = None,
    ) -> dict:
        profile = repo.get_profile(uid)
        if profile:
            return profile
        entity = UserEntity(
            uid=uid, email=email, display_name=display_name, photo_url=photo_url
        )
        return repo.create_from_entity(entity)

    def get_profile(self, uid: str) -> dict:
        profile = repo.get_profile(uid)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
            )
        return profile

    def set_role(self, uid: str, role: UserRole) -> dict:
        profile = repo.get_profile(uid)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found. Complete signup first.",
            )
        return repo.update_profile(uid, {"role": role.value})

    def update_profile(self, uid: str, data: dict) -> dict:
        if not repo.profile_exists(uid):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
            )
        return repo.update_profile(uid, data)
