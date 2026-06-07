import logging
from typing import Optional

from app.core.exceptions import NotFoundException, ForbiddenException
from app.models.job_posting import JobOrInternshipPosting
from app.repositories.job_posting import JobPostingRepository

logger = logging.getLogger("verifai")


class JobPostingService:
    def __init__(self):
        self.repo = JobPostingRepository()

    async def create_posting(self, company_id: str, recruiter_id: str, firebase_uid: str, **kwargs) -> JobOrInternshipPosting:
        posting = await self.repo.create_posting(
            company_id=company_id,
            recruiter_id=recruiter_id,
            firebase_uid=firebase_uid,
            **kwargs,
        )
        logger.info("Job posting created: %s for company %s", posting.title, company_id)
        return posting

    async def get_posting_by_id(self, posting_id: str) -> JobOrInternshipPosting:
        data = await self.repo.get(posting_id)
        if not data:
            raise NotFoundException("Job posting not found", error_code="POSTING_NOT_FOUND")
        return JobOrInternshipPosting(**data)

    async def update_posting(self, posting_id: str, firebase_uid: str, **kwargs) -> JobOrInternshipPosting:
        posting = await self.get_posting_by_id(posting_id)
        if posting.firebase_uid != firebase_uid:
            raise ForbiddenException(
                "You can only update your own postings",
                error_code="FORBIDDEN",
            )
        data = {k: v for k, v in kwargs.items() if v is not None}
        if not data:
            return posting
        success = await self.repo.update(posting_id, **data)
        if not success:
            raise NotFoundException("Job posting not found", error_code="POSTING_NOT_FOUND")
        updated = await self.repo.get(posting_id)
        return JobOrInternshipPosting(**updated) if updated else posting

    async def delete_posting(self, posting_id: str, firebase_uid: str) -> None:
        posting = await self.get_posting_by_id(posting_id)
        if posting.firebase_uid != firebase_uid:
            raise ForbiddenException(
                "You can only delete your own postings",
                error_code="FORBIDDEN",
            )
        success = await self.repo.update(posting_id, is_active=False)
        if not success:
            raise NotFoundException("Job posting not found", error_code="POSTING_NOT_FOUND")
        logger.info("Job posting deactivated: %s", posting_id)

    async def list_by_recruiter(self, recruiter_id: str) -> list[JobOrInternshipPosting]:
        return await self.repo.get_by_recruiter_id(recruiter_id)
