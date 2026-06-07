import logging
from typing import Optional

from app.core.exceptions import NotFoundException, ConflictException
from app.models.student_saved_company import StudentSavedCompany
from app.repositories.student_saved_company import StudentSavedCompanyRepository
from app.repositories.company_profile import CompanyProfileRepository
from app.repositories.student_submission_summary import StudentSubmissionSummaryRepository

logger = logging.getLogger("verifai")


class StudentSavedCompanyService:
    def __init__(self):
        self.repo = StudentSavedCompanyRepository()
        self.company_repo = CompanyProfileRepository()
        self.summary_repo = StudentSubmissionSummaryRepository()

    async def save_company(self, student_id: str, student_firebase_uid: str, company_id: str) -> StudentSavedCompany:
        company = await self.company_repo.get(company_id)
        if not company:
            raise NotFoundException("Company not found", error_code="COMPANY_NOT_FOUND")

        existing = await self.repo.get_by_student_and_company(student_id, company_id)
        if existing:
            raise ConflictException(
                "Company already saved",
                error_code="COMPANY_ALREADY_SAVED",
            )

        saved = await self.repo.create_saved(
            student_id=student_id,
            student_firebase_uid=student_firebase_uid,
            company_id=company_id,
        )
        await self._update_saved_count(student_id)
        return saved

    async def unsave_company(self, student_id: str, company_id: str) -> None:
        success = await self.repo.delete_by_student_and_company(student_id, company_id)
        if not success:
            raise NotFoundException("Saved company not found", error_code="SAVED_COMPANY_NOT_FOUND")
        await self._update_saved_count(student_id)

    async def list_saved_companies(self, student_id: str) -> list[StudentSavedCompany]:
        return await self.repo.get_by_student(student_id)

    async def _update_saved_count(self, student_id: str) -> None:
        try:
            count = await self.repo.count_by_student(student_id)
            existing = await self.summary_repo.get_by_student_id(student_id)
            if existing:
                await self.summary_repo.update(existing.id, saved_companies_count=count)
        except Exception as e:
            logger.warning("Failed to update saved company count: %s", e)
