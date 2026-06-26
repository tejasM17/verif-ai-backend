from fastapi import HTTPException, status

from app.repositories.application_repository import (
    ApplicationRepository,
    DuplicateApplicationError,
)
from app.repositories.company_repository import CompanyRepository
from app.repositories.job_repository import JobRepository
from app.repositories.user_repository import UserRepository
from app.schemas.application import ApplicationStatus, ApplicationSubmit


class ApplicationService:
    def __init__(self):
        self.repo = ApplicationRepository()
        self.user_repo = UserRepository()
        self.company_repo = CompanyRepository()
        self.job_repo = JobRepository()

    def submit(self, student_uid: str, payload: ApplicationSubmit) -> dict:
        company = self.company_repo.get_by_uid(payload.company_uid)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found",
            )
        resume = self.user_repo.get_resume(payload.resume_uid)
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found. Upload your resume first.",
            )
        student_profile = self.user_repo.get_profile(student_uid) or {}
        if payload.resume_uid != student_uid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Resume does not belong to the current student.",
            )

        # Optional job_uid — verify the job (if provided) belongs to this company
        job_uid = payload.job_uid
        if job_uid:
            job = self.job_repo.get_by_uid(job_uid)
            if not job:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Job not found",
                )
            if job.get("company_uid") != payload.company_uid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Job does not belong to the specified company.",
                )

        recruiter_uid = payload.company_uid
        try:
            application = self.repo.create(
                student_uid=student_uid,
                recruiter_uid=recruiter_uid,
                company_uid=payload.company_uid,
                resume_uid=payload.resume_uid,
                why_appoint=payload.why_appoint,
                job_uid=job_uid,
            )
        except DuplicateApplicationError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already applied to this company.",
            )
        return application

    def get_for_student_or_recruiter(
        self, app_id: str, current_uid: str, role: str
    ) -> dict:
        application = self.repo.get_by_id(app_id)
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Application not found"
            )
        if role == "student" and application["student_uid"] != current_uid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this application",
            )
        if role == "recruiter" and application["recruiter_uid"] != current_uid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this application",
            )
        return application

    def list_for_recruiter(
        self, recruiter_uid: str, status_filter: str | None, limit: int, skip: int
    ) -> tuple[list[dict], int]:
        valid_statuses = {s.value for s in ApplicationStatus}
        if status_filter and status_filter not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Allowed: {sorted(valid_statuses)}",
            )
        apps, total = self.repo.list_by_recruiter(
            recruiter_uid=recruiter_uid,
            status=status_filter,
            limit=limit,
            skip=skip,
        )
        return self._enrich_for_recruiter(apps), total

    def list_for_student(
        self, student_uid: str, limit: int, skip: int
    ) -> tuple[list[dict], int]:
        apps, total = self.repo.list_by_student(
            student_uid=student_uid, limit=limit, skip=skip
        )
        return self._enrich_for_student(apps), total

    def update_status(
        self,
        recruiter_uid: str,
        app_id: str,
        new_status: ApplicationStatus,
        note: str | None,
    ) -> dict:
        application = self.repo.get_by_id(app_id)
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Application not found"
            )
        if application["recruiter_uid"] != recruiter_uid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this application",
            )
        updated = self.repo.update_status(app_id, new_status, note)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Application not found"
            )
        return updated

    def _enrich_for_recruiter(self, apps: list[dict]) -> list[dict]:
        enriched = []
        for app in apps:
            student = self.user_repo.get_profile(app["student_uid"]) or {}
            job_uid = app.get("job_uid")
            job = self.job_repo.get_by_uid(job_uid) if job_uid else None
            enriched.append(
                {
                    **app,
                    "student_display_name": student.get("display_name"),
                    "student_email": student.get("email"),
                    "student_photo_url": student.get("photo_url"),
                    "student_skills": student.get("skills", []),
                    "resume_url": f"/resume/file/{app['resume_uid']}",
                    "company_name": None,
                    "company_role": None,
                    "company_location": None,
                    "company_logo_url": None,
                    "job_uid": job_uid,
                    "job_title": (job or {}).get("title"),
                }
            )
        return enriched

    def _enrich_for_student(self, apps: list[dict]) -> list[dict]:
        enriched = []
        for app in apps:
            company = self.company_repo.get_by_uid(app["company_uid"]) or {}
            job_uid = app.get("job_uid")
            job = self.job_repo.get_by_uid(job_uid) if job_uid else None
            enriched.append(
                {
                    **app,
                    "company_name": company.get("company_name"),
                    "company_role": company.get("role"),
                    "company_location": company.get("location"),
                    "company_logo_url": company.get("logo_url"),
                    "resume_url": f"/resume/file/{app['resume_uid']}",
                    "student_uid": app["student_uid"],
                    "student_display_name": None,
                    "student_email": None,
                    "student_photo_url": None,
                    "student_skills": [],
                    "job_uid": job_uid,
                    "job_title": (job or {}).get("title"),
                }
            )
        return enriched

    def delete_for_student(self, student_uid: str, app_id: str) -> bool:
        application = self.repo.get_by_id(app_id)
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Application not found"
            )
        if application.get("student_uid") != student_uid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this application",
            )
        deleted = self.repo.delete(app_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Application not found"
            )
        return True


__all__ = ["ApplicationService", "ApplicationStatus"]