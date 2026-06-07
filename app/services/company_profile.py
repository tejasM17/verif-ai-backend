import logging
from datetime import datetime, timezone
from typing import Optional

from app.core.exceptions import NotFoundException, ConflictException, ForbiddenException
from app.models.company_profile import CompanyProfile
from app.models.job_posting import JobOrInternshipPosting
from app.repositories.company_profile import CompanyProfileRepository
from app.repositories.job_posting import JobPostingRepository

logger = logging.getLogger("verifai")


class CompanyProfileService:
    def __init__(self):
        self.repo = CompanyProfileRepository()
        self.posting_repo = JobPostingRepository()

    async def create_company(self, recruiter_id: str, firebase_uid: str, **kwargs) -> CompanyProfile:
        existing = await self.repo.get_by_firebase_uid(firebase_uid)
        if existing:
            raise ConflictException(
                "Company profile already exists for this recruiter",
                error_code="COMPANY_ALREADY_EXISTS",
            )
        company = await self.repo.create_company(
            recruiter_id=recruiter_id,
            firebase_uid=firebase_uid,
            **kwargs,
        )
        logger.info("Company profile created: %s by recruiter %s", company.company_name, firebase_uid)
        return company

    async def get_company_by_id(self, company_id: str) -> CompanyProfile:
        data = await self.repo.get(company_id)
        if not data:
            raise NotFoundException("Company not found", error_code="COMPANY_NOT_FOUND")
        return CompanyProfile(**data)

    async def get_company_by_firebase_uid(self, firebase_uid: str) -> Optional[CompanyProfile]:
        return await self.repo.get_by_firebase_uid(firebase_uid)

    async def update_company(self, company_id: str, firebase_uid: str, **kwargs) -> CompanyProfile:
        company = await self.get_company_by_id(company_id)
        if company.firebase_uid != firebase_uid:
            raise ForbiddenException(
                "You can only update your own company profile",
                error_code="FORBIDDEN",
            )
        data = {k: v for k, v in kwargs.items() if v is not None}
        if not data:
            return company
        success = await self.repo.update(company_id, **data)
        if not success:
            raise NotFoundException("Company not found", error_code="COMPANY_NOT_FOUND")
        updated = await self.repo.get(company_id)
        return CompanyProfile(**updated) if updated else company

    async def list_companies(
        self,
        page: int = 1,
        page_size: int = 20,
        tech_stack: Optional[str] = None,
        skills: Optional[str] = None,
        hiring_status: Optional[str] = None,
        has_internships: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> tuple[list[CompanyProfile], int]:
        all_companies = await self.repo.get_all_active(skip=0, limit=10000)
        filtered = []
        for c in all_companies:
            if not c.is_active:
                continue
            if hiring_status and c.hiring_status != hiring_status:
                continue
            if has_internships is not None and c.has_internships != has_internships:
                continue
            if tech_stack:
                ts_list = [t.strip().lower() for t in tech_stack.split(",")]
                company_ts = [t.lower() for t in c.tech_stack]
                if not any(t in company_ts for t in ts_list):
                    continue
            if skills:
                sk_list = [s.strip().lower() for s in skills.split(",")]
                company_sk = [s.lower() for s in c.required_skills]
                if not any(s in company_sk for s in sk_list):
                    continue
            if search:
                q = search.lower()
                if q not in c.company_name.lower() and (not c.summary or q not in c.summary.lower()):
                    continue
            filtered.append(c)

        total = len(filtered)
        start = (page - 1) * page_size
        end = start + page_size
        page_data = filtered[start:end]
        return page_data, total

    async def get_company_detail(self, company_id: str) -> tuple[CompanyProfile, list[JobOrInternshipPosting]]:
        company = await self.get_company_by_id(company_id)
        postings = await self.posting_repo.get_open_by_company_id(company_id)
        return company, postings

    async def get_open_postings(self, company_id: str) -> list[JobOrInternshipPosting]:
        return await self.posting_repo.get_open_by_company_id(company_id)
