from typing import Optional
from app.repositories.base import BaseRepository
from app.models.company_profile import CompanyProfile


class CompanyProfileRepository(BaseRepository):
    collection_name = "companies"

    async def get_by_firebase_uid(self, firebase_uid: str) -> Optional[CompanyProfile]:
        data = await self.get_by_field("firebase_uid", firebase_uid)
        return CompanyProfile(**data) if data else None

    async def get_by_recruiter_id(self, recruiter_id: str) -> Optional[CompanyProfile]:
        data = await self.get_by_field("recruiter_id", recruiter_id)
        return CompanyProfile(**data) if data else None

    async def create_company(self, **kwargs) -> CompanyProfile:
        _, data = await self.create(**kwargs)
        return CompanyProfile(**data)

    async def get_all_active(self, skip: int = 0, limit: int = 100) -> list[CompanyProfile]:
        data_list = await self.get_all_by_field("is_active", True, skip, limit)
        return [CompanyProfile(**d) for d in data_list]

    async def count_active(self) -> int:
        all_active = await self.get_all_by_field("is_active", True, 0, 10000)
        return len(all_active)
