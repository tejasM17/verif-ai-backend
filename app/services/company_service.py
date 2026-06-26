from fastapi import HTTPException, status

from app.domain.enums.role import UserRole
from app.repositories.company_repository import CompanyRepository
from app.repositories.user_repository import UserRepository
from app.schemas.company import CompanyCreate, CompanyUpdate


class CompanyService:
    def __init__(self):
        self.repo = CompanyRepository()
        self.user_repo = UserRepository()

    def _sync_base_profile(
        self,
        uid: str,
        company_name: str | None,
        role_title: str | None,
        location: str | None,
    ) -> None:
        payload: dict = {}
        if company_name is not None:
            payload["company_name"] = company_name
        if role_title is not None:
            payload["role_title"] = role_title
        if location is not None:
            payload["location"] = location
        if payload and self.user_repo.profile_exists(uid):
            self.user_repo.update_profile(uid, payload)

    def create_or_update_my_company(self, uid: str, data: CompanyCreate) -> dict:
        company = self.repo.upsert(uid, data.model_dump(exclude_unset=False))
        self._sync_base_profile(
            uid,
            data.company_name,
            data.role,
            data.location,
        )
        return company

    def update_my_company(self, uid: str, data: CompanyUpdate) -> dict:
        existing = self.repo.get_by_uid(uid)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company profile not found",
            )
        filtered = data.model_dump(exclude_unset=True)
        if not filtered:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid company fields provided",
            )
        company = self.repo.upsert(uid, filtered)
        self._sync_base_profile(
            uid,
            filtered.get("company_name", existing.get("company_name")),
            filtered.get("role", existing.get("role")),
            filtered.get("location", existing.get("location")),
        )
        return company

    def get_my_company(self, uid: str) -> dict:
        company = self.repo.get_by_uid(uid)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company profile not found. Create one first.",
            )
        return company

    def get_company_by_uid(self, uid: str) -> dict:
        company = self.repo.get_by_uid(uid)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
            )
        return company

    def list_companies(self, limit: int, skip: int) -> tuple[list[dict], int]:
        return self.repo.list_all(limit=limit, skip=skip)

    def search_companies(
        self,
        q: str | None,
        location: str | None,
        role: str | None,
        limit: int,
        skip: int,
    ) -> tuple[list[dict], int]:
        return self.repo.search(q=q, location=location, role=role, limit=limit, skip=skip)


__all__ = ["CompanyService", "UserRole"]