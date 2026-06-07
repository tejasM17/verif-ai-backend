from fastapi import APIRouter, Depends, File, UploadFile, Response
from fastapi import status as http_status

from app.core.dependencies import get_current_student, get_current_recruiter, get_current_user
from app.core.response import success_response
from app.core.exceptions import ValidationException
from app.models.student import Student
from app.models.recruiter import Recruiter
from app.schemas.file_upload import FileUploadResponse
from app.services.file_service import FileService

router = APIRouter(tags=["Application Files"])


@router.post("/applications/{application_id}/resume", status_code=http_status.HTTP_201_CREATED)
async def upload_resume(
    application_id: str,
    file: UploadFile = File(...),
    student: Student = Depends(get_current_student),
):
    if not file.filename or not file.filename.strip():
        raise ValidationException("No file selected", error_code="NO_FILE")

    content_type = file.content_type or "application/octet-stream"
    file_bytes = await file.read()
    file_size = len(file_bytes)

    service = FileService()
    doc = await service.upload(
        student=student,
        application_id=application_id,
        file_type="resume",
        filename=file.filename,
        content_type=content_type,
        file_size=file_size,
        file_data=file_bytes,
    )

    return success_response(
        data=FileUploadResponse(
            file_id=doc["file_id"],
            application_id=doc["application_id"],
            original_filename=doc["original_filename"],
            content_type=doc["content_type"],
            file_size=doc["file_size"],
            file_type=doc["file_type"],
            uploaded_at=doc["uploaded_at"],
            updated_at=doc["updated_at"],
        ).model_dump(mode="json"),
        message="Resume uploaded successfully",
        status_code=http_status.HTTP_201_CREATED,
    )


@router.post("/applications/{application_id}/certificate", status_code=http_status.HTTP_201_CREATED)
async def upload_certificate(
    application_id: str,
    file: UploadFile = File(...),
    student: Student = Depends(get_current_student),
):
    if not file.filename or not file.filename.strip():
        raise ValidationException("No file selected", error_code="NO_FILE")

    content_type = file.content_type or "application/octet-stream"
    file_bytes = await file.read()
    file_size = len(file_bytes)

    service = FileService()
    doc = await service.upload(
        student=student,
        application_id=application_id,
        file_type="certificate",
        filename=file.filename,
        content_type=content_type,
        file_size=file_size,
        file_data=file_bytes,
    )

    return success_response(
        data=FileUploadResponse(
            file_id=doc["file_id"],
            application_id=doc["application_id"],
            original_filename=doc["original_filename"],
            content_type=doc["content_type"],
            file_size=doc["file_size"],
            file_type=doc["file_type"],
            uploaded_at=doc["uploaded_at"],
            updated_at=doc["updated_at"],
        ).model_dump(mode="json"),
        message="Certificate uploaded successfully",
        status_code=http_status.HTTP_201_CREATED,
    )


@router.get("/applications/{application_id}/resume")
async def download_resume(
    application_id: str,
    current_user: dict = Depends(get_current_user),
):
    requester_role = current_user.get("role", "")
    requester_id = current_user.get("sub", "")
    firebase_uid = current_user.get("firebase_uid", "")

    service = FileService()
    file_data, content_type, original_filename = await service.download(
        application_id=application_id,
        file_type="resume",
        requester_id=requester_id,
        requester_role=requester_role,
        firebase_uid=firebase_uid,
    )

    return Response(
        content=file_data,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{original_filename}"',
            "Content-Type": content_type,
        },
    )


@router.get("/applications/{application_id}/certificate")
async def download_certificate(
    application_id: str,
    current_user: dict = Depends(get_current_user),
):
    requester_role = current_user.get("role", "")
    requester_id = current_user.get("sub", "")
    firebase_uid = current_user.get("firebase_uid", "")

    service = FileService()
    file_data, content_type, original_filename = await service.download(
        application_id=application_id,
        file_type="certificate",
        requester_id=requester_id,
        requester_role=requester_role,
        firebase_uid=firebase_uid,
    )

    return Response(
        content=file_data,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{original_filename}"',
            "Content-Type": content_type,
        },
    )


@router.delete("/applications/{application_id}/resume")
async def delete_resume(
    application_id: str,
    student: Student = Depends(get_current_student),
):
    service = FileService()
    await service.delete(
        application_id=application_id,
        file_type="resume",
        requester_id=student.id,
        requester_role="student",
        firebase_uid=student.firebase_uid,
    )
    return success_response(message="Resume deleted successfully")


@router.delete("/applications/{application_id}/certificate")
async def delete_certificate(
    application_id: str,
    student: Student = Depends(get_current_student),
):
    service = FileService()
    await service.delete(
        application_id=application_id,
        file_type="certificate",
        requester_id=student.id,
        requester_role="student",
        firebase_uid=student.firebase_uid,
    )
    return success_response(message="Certificate deleted successfully")
