import logging
from datetime import datetime, timezone
from typing import Optional

from app.core.exceptions import (
    NotFoundException,
    ConflictException,
    ForbiddenException,
    ValidationException,
)
from app.models.application import Application, ApplicationStatusHistory
from app.models.student import Student
from app.models.job_posting import JobOrInternshipPosting
from app.models.company_profile import CompanyProfile
from app.repositories.application import ApplicationRepository
from app.repositories.student import StudentRepository
from app.repositories.job_posting import JobPostingRepository
from app.repositories.company_profile import CompanyProfileRepository
from app.repositories.student_submission_summary import StudentSubmissionSummaryRepository
from app.repositories.file_repository import FileRepository

logger = logging.getLogger("verifai")

VALID_STATUSES = {"draft", "submitted", "reviewing", "selected", "rejected", "request_changes"}
VALID_TRANSITIONS = {
    "draft": {"submitted"},
    "submitted": {"reviewing", "rejected", "request_changes"},
    "reviewing": {"selected", "rejected", "request_changes"},
    "selected": {"rejected"},
    "rejected": set(),
    "request_changes": {"submitted", "reviewing", "rejected"},
}


class ApplicationService:
    def __init__(self):
        self.repo = ApplicationRepository()
        self.student_repo = StudentRepository()
        self.posting_repo = JobPostingRepository()
        self.company_repo = CompanyProfileRepository()
        self.summary_repo = StudentSubmissionSummaryRepository()
        self.file_repo = FileRepository()

    async def create_application(
        self,
        student: Student,
        company_id: str,
        posting_id: str,
        github_project_link: str,
        cover_letter: Optional[str] = None,
    ) -> Application:
        company = await self.company_repo.get(company_id)
        if not company or not company.get("is_active"):
            raise NotFoundException("Company not found", error_code="COMPANY_NOT_FOUND")

        posting_data = await self.posting_repo.get(posting_id)
        if not posting_data or not posting_data.get("is_active"):
            raise NotFoundException("Job posting not found", error_code="POSTING_NOT_FOUND")
        posting = JobOrInternshipPosting(**posting_data)

        if posting.status != "open":
            raise ValidationException(
                "This posting is no longer accepting applications",
                error_code="POSTING_CLOSED",
            )

        existing = await self.repo.get_by_posting_and_student(posting_id, student.id)
        if existing:
            raise ConflictException(
                "You have already applied to this position",
                error_code="DUPLICATE_APPLICATION",
            )

        now = datetime.now(timezone.utc)
        history_entry = ApplicationStatusHistory(
            status="draft",
            changed_by=student.firebase_uid,
            changed_by_role="student",
            reason="Application draft created",
            timestamp=now,
        )

        application = await self.repo.create_application(
            student_id=student.id,
            student_firebase_uid=student.firebase_uid,
            company_id=company_id,
            posting_id=posting_id,
            github_project_link=github_project_link,
            cover_letter=cover_letter,
            status="draft",
            status_history=[history_entry.model_dump(mode="json")],
        )
        logger.info(
            "Application draft created: student=%s posting=%s id=%s",
            student.id, posting_id, application.id,
        )
        return application

    async def submit_application(
        self,
        application_id: str,
        student: Student,
    ) -> Application:
        data = await self.repo.get(application_id)
        if not data:
            raise NotFoundException("Application not found", error_code="APPLICATION_NOT_FOUND")
        app = Application(**data)

        if app.student_id != student.id:
            raise ForbiddenException(
                "You can only submit your own applications",
                error_code="FORBIDDEN",
            )

        if app.status != "draft":
            raise ValidationException(
                f"Cannot submit application with status '{app.status}'",
                error_code="INVALID_STATUS",
            )

        resume_exists = await self.file_repo.exists_by_application_and_type(application_id, "resume")
        if not resume_exists:
            raise ValidationException(
                "Resume is required before submitting an application",
                error_code="RESUME_REQUIRED",
            )

        if not app.github_project_link:
            raise ValidationException(
                "GitHub project link is required before submitting an application",
                error_code="GITHUB_REQUIRED",
            )

        now = datetime.now(timezone.utc)
        history_entry = ApplicationStatusHistory(
            status="submitted",
            changed_by=student.firebase_uid,
            changed_by_role="student",
            reason="Application submitted",
            timestamp=now,
        )

        current_history = app.status_history or []
        updated_history = current_history + [history_entry.model_dump(mode="json")]

        success = await self.repo.update(
            application_id,
            status="submitted",
            status_history=updated_history,
            submitted_at=now,
        )
        if not success:
            raise NotFoundException("Application not found", error_code="APPLICATION_NOT_FOUND")

        logger.info(
            "Application submitted: student=%s application=%s",
            student.id, application_id,
        )

        await self._update_summary(student.id, student.firebase_uid)

        updated = await self.repo.get(application_id)
        return Application(**updated) if updated else app

    async def get_student_application(self, application_id: str, student_id: str) -> Application:
        data = await self.repo.get(application_id)
        if not data:
            raise NotFoundException("Application not found", error_code="APPLICATION_NOT_FOUND")
        app = Application(**data)
        if app.student_id != student_id:
            raise ForbiddenException(
                "You can only view your own applications",
                error_code="FORBIDDEN",
            )
        return app

    async def list_student_applications(
        self, student_id: str, page: int = 1, page_size: int = 20,
    ) -> tuple[list[Application], int]:
        all_apps = await self.repo.get_by_student_id(student_id)
        total = len(all_apps)
        start = (page - 1) * page_size
        end = start + page_size
        return all_apps[start:end], total

    async def get_recruiter_application(
        self, application_id: str, firebase_uid: str,
    ) -> tuple[Application, Student, JobOrInternshipPosting]:
        data = await self.repo.get(application_id)
        if not data:
            raise NotFoundException("Application not found", error_code="APPLICATION_NOT_FOUND")
        app = Application(**data)

        company = await self.company_repo.get(app.company_id)
        if not company or company.get("firebase_uid") != firebase_uid:
            raise ForbiddenException(
                "You can only view applications for your own company",
                error_code="FORBIDDEN",
            )

        student_data = await self.student_repo.get(app.student_id)
        student = Student(**student_data) if student_data else None

        posting_data = await self.posting_repo.get(app.posting_id)
        posting = JobOrInternshipPosting(**posting_data) if posting_data else None

        return app, student, posting

    async def list_recruiter_applications(
        self, firebase_uid: str, page: int = 1, page_size: int = 20,
    ) -> tuple[list[Application], int, CompanyProfile]:
        company = await self.company_repo.get_by_firebase_uid(firebase_uid)
        if not company:
            raise NotFoundException(
                "No company profile found. Create one first.",
                error_code="COMPANY_NOT_FOUND",
            )
        all_apps = await self.repo.get_by_company_id(company.id)
        total = len(all_apps)
        start = (page - 1) * page_size
        end = start + page_size
        return all_apps[start:end], total, company

    async def update_application_status(
        self,
        application_id: str,
        firebase_uid: str,
        new_status: str,
        reason: Optional[str] = None,
    ) -> Application:
        data = await self.repo.get(application_id)
        if not data:
            raise NotFoundException("Application not found", error_code="APPLICATION_NOT_FOUND")
        app = Application(**data)

        company = await self.company_repo.get(app.company_id)
        if not company or company.get("firebase_uid") != firebase_uid:
            raise ForbiddenException(
                "You can only update applications for your own company",
                error_code="FORBIDDEN",
            )

        if new_status not in VALID_STATUSES:
            raise ValidationException(
                f"Invalid status: {new_status}",
                error_code="INVALID_STATUS",
            )

        valid_next = VALID_TRANSITIONS.get(app.status, set())
        if new_status not in valid_next:
            raise ValidationException(
                f"Cannot transition from '{app.status}' to '{new_status}'",
                error_code="INVALID_STATUS_TRANSITION",
            )

        now = datetime.now(timezone.utc)
        history_entry = ApplicationStatusHistory(
            status=new_status,
            changed_by=firebase_uid,
            changed_by_role="recruiter",
            reason=reason or f"Status changed to {new_status}",
            timestamp=now,
        )

        current_history = app.status_history or []
        updated_history = current_history + [history_entry.model_dump(mode="json")]

        success = await self.repo.update(
            application_id,
            status=new_status,
            status_history=updated_history,
        )
        if not success:
            raise NotFoundException("Application not found", error_code="APPLICATION_NOT_FOUND")

        if app.student_id:
            await self._update_summary(app.student_id, app.student_firebase_uid)

        updated = await self.repo.get(application_id)
        return Application(**updated) if updated else app

    async def _update_summary(self, student_id: str, firebase_uid: str) -> None:
        try:
            total = await self.repo.count_by_student(student_id)
            submitted = await self.repo.count_by_student_and_status(student_id, "submitted")
            reviewing = await self.repo.count_by_student_and_status(student_id, "reviewing")
            selected = await self.repo.count_by_student_and_status(student_id, "selected")
            rejected = await self.repo.count_by_student_and_status(student_id, "rejected")

            existing = await self.summary_repo.get_by_student_id(student_id)
            if existing:
                await self.summary_repo.update(
                    existing.id,
                    total_applications=total,
                    submitted_count=submitted,
                    reviewing_count=reviewing,
                    selected_count=selected,
                    rejected_count=rejected,
                )
            else:
                await self.summary_repo.create_summary(
                    student_id=student_id,
                    student_firebase_uid=firebase_uid,
                    total_applications=total,
                    submitted_count=submitted,
                    reviewing_count=reviewing,
                    selected_count=selected,
                    rejected_count=rejected,
                )
        except Exception as e:
            logger.warning("Failed to update submission summary: %s", e)
