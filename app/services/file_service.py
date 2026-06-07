import logging
from typing import Optional

from app.core.exceptions import NotFoundException, ForbiddenException, ConflictException
from app.models.student import Student
from app.models.recruiter import Recruiter
from app.repositories.file_repository import FileRepository
from app.repositories.audit_repository import AuditRepository
from app.repositories.application import ApplicationRepository
from app.repositories.company_profile import CompanyProfileRepository
from app.utils.file_validator import validate_upload

logger = logging.getLogger("verifai")


class FileService:

    def __init__(self):
        self.file_repo = FileRepository()
        self.audit_repo = AuditRepository()
        self.application_repo = ApplicationRepository()
        self.company_repo = CompanyProfileRepository()

    async def upload(
        self,
        student: Student,
        application_id: str,
        file_type: str,
        filename: str,
        content_type: str,
        file_size: int,
        file_data: bytes,
    ) -> dict:
        safe_name = validate_upload(filename, content_type, file_size, file_type)

        app_data = await self.application_repo.get(application_id)
        if not app_data:
            raise NotFoundException("Application not found", error_code="APPLICATION_NOT_FOUND")

        await self._check_ownership(app_data, student.id, "student", student.firebase_uid, application_id, file_type, "upload")

        existing = await self.file_repo.find_by_application_and_type(application_id, file_type)
        action = "replace" if existing else "upload"

        doc = await self.file_repo.create(
            application_id=application_id,
            student_id=student.id,
            firebase_uid=student.firebase_uid,
            original_filename=safe_name,
            content_type=content_type,
            file_size=file_size,
            file_type=file_type,
            file_data=file_data,
        )

        if not doc:
            raise ConflictException("Failed to store file", error_code="UPLOAD_FAILED")

        await self.application_repo.update(application_id, **{f"{file_type}_file_id": doc["file_id"]})

        await self.audit_repo.log(
            action=action,
            actor_id=student.id,
            actor_role="student",
            target_type=file_type,
            application_id=application_id,
            details=f"{action}: {safe_name} ({file_size} bytes, {content_type})",
        )

        logger.info(
            "File %s: student=%s application=%s type=%s file=%s size=%d",
            action, student.id, application_id, file_type, safe_name, file_size,
        )

        return doc

    async def download(
        self,
        application_id: str,
        file_type: str,
        requester_id: str,
        requester_role: str,
        firebase_uid: str,
    ) -> tuple[bytes, str, str]:
        app_data = await self.application_repo.get(application_id)
        if not app_data:
            raise NotFoundException("Application not found", error_code="APPLICATION_NOT_FOUND")

        await self._check_ownership(app_data, requester_id, requester_role, firebase_uid, application_id, file_type, "download")

        doc = await self.file_repo.find_by_application_and_type(application_id, file_type)
        if not doc:
            raise NotFoundException(
                f"{file_type.capitalize()} not found for this application",
                error_code=f"{file_type.upper()}_NOT_FOUND",
            )

        await self.audit_repo.log(
            action="download",
            actor_id=requester_id,
            actor_role=requester_role,
            target_type=file_type,
            application_id=application_id,
            details=f"Downloaded: {doc.get('original_filename', 'unknown')}",
        )

        logger.info(
            "File download: %s=%s application=%s type=%s",
            requester_role, requester_id, application_id, file_type,
        )

        return doc["file_data"], doc["content_type"], doc.get("original_filename", f"{file_type}.bin")

    async def delete(
        self,
        application_id: str,
        file_type: str,
        requester_id: str,
        requester_role: str,
        firebase_uid: str,
    ) -> None:
        app_data = await self.application_repo.get(application_id)
        if not app_data:
            raise NotFoundException("Application not found", error_code="APPLICATION_NOT_FOUND")

        await self._check_ownership(app_data, requester_id, requester_role, firebase_uid, application_id, file_type, "delete")

        existing = await self.file_repo.find_by_application_and_type(application_id, file_type)
        if not existing:
            raise NotFoundException(
                f"{file_type.capitalize()} not found for this application",
                error_code=f"{file_type.upper()}_NOT_FOUND",
            )

        deleted = await self.file_repo.delete_by_application_and_type(application_id, file_type)
        if not deleted:
            raise ConflictException("Failed to delete file", error_code="DELETE_FAILED")

        await self.application_repo.update(application_id, **{f"{file_type}_file_id": None})

        await self.audit_repo.log(
            action="delete",
            actor_id=requester_id,
            actor_role=requester_role,
            target_type=file_type,
            application_id=application_id,
            details=f"Deleted: {existing.get('original_filename', 'unknown')}",
        )

        logger.info(
            "File deleted: %s=%s application=%s type=%s",
            requester_role, requester_id, application_id, file_type,
        )

    async def _check_ownership(
        self,
        app_data: dict,
        requester_id: str,
        requester_role: str,
        firebase_uid: str,
        application_id: str,
        file_type: str,
        action: str,
    ) -> None:
        if requester_role == "student":
            if app_data.get("student_id") != requester_id:
                await self.audit_repo.log(
                    action="unauthorized_access",
                    actor_id=requester_id,
                    actor_role=requester_role,
                    target_type=file_type,
                    application_id=application_id,
                    details=f"Student {requester_id} attempted to {action} application {application_id}",
                )
                raise ForbiddenException(
                    "You can only access your own application files",
                    error_code="FORBIDDEN",
                )
        elif requester_role == "recruiter":
            company = await self.company_repo.get_by_firebase_uid(firebase_uid)
            if not company or company.id != app_data.get("company_id"):
                await self.audit_repo.log(
                    action="unauthorized_access",
                    actor_id=requester_id,
                    actor_role=requester_role,
                    target_type=file_type,
                    application_id=application_id,
                    details=f"Recruiter {requester_id} attempted to {action} application {application_id}",
                )
                raise ForbiddenException(
                    "You can only access applications for your own company",
                    error_code="FORBIDDEN",
                )
