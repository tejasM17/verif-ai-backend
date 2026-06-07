from typing import Optional
from app.repositories.base import BaseRepository
from app.models.job_posting import JobOrInternshipPosting


class JobPostingRepository(BaseRepository):
    collection_name = "job_postings"

    async def get_by_company_id(self, company_id: str, skip: int = 0, limit: int = 100) -> list[JobOrInternshipPosting]:
        data_list = await self.get_all_by_field("company_id", company_id, skip, limit)
        return [JobOrInternshipPosting(**d) for d in data_list if d.get("is_active", True)]

    async def get_open_by_company_id(self, company_id: str, skip: int = 0, limit: int = 100) -> list[JobOrInternshipPosting]:
        filters = [("company_id", "==", company_id), ("status", "==", "open"), ("is_active", "==", True)]
        data_list = await self.filter_by(filters, skip, limit)
        return [JobOrInternshipPosting(**d) for d in data_list]

    async def get_by_recruiter_id(self, recruiter_id: str, skip: int = 0, limit: int = 100) -> list[JobOrInternshipPosting]:
        data_list = await self.get_all_by_field("recruiter_id", recruiter_id, skip, limit)
        return [JobOrInternshipPosting(**d) for d in data_list]

    async def create_posting(self, **kwargs) -> JobOrInternshipPosting:
        _, data = await self.create(**kwargs)
        return JobOrInternshipPosting(**data)
