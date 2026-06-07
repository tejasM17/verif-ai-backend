from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_student
from app.core.response import success_response
from app.core.exceptions import ValidationException
from app.models.student import Student
from app.schemas.application import ApplicationCreateRequest, ApplicationStudentResponse
from app.services.application import ApplicationService

router = APIRouter(tags=["Applications"])


@router.post("/applications", status_code=201)
async def create_application(
    request: ApplicationCreateRequest,
    student: Student = Depends(get_current_student),
):
    if not request.github_project_link.strip():
        raise ValidationException("GitHub project link is required", error_code="GITHUB_REQUIRED")

    service = ApplicationService()
    application = await service.create_application(
        student=student,
        company_id=request.company_id,
        posting_id=request.posting_id,
        github_project_link=request.github_project_link.strip(),
        cover_letter=request.cover_letter.strip() if request.cover_letter else None,
    )
    return success_response(
        data=ApplicationStudentResponse(**application.model_dump()).model_dump(mode="json"),
        message="Application draft created successfully. Upload resume and submit.",
        status_code=201,
    )


@router.post("/applications/{application_id}/submit")
async def submit_application(
    application_id: str,
    student: Student = Depends(get_current_student),
):
    service = ApplicationService()
    application = await service.submit_application(
        application_id=application_id,
        student=student,
    )
    return success_response(
        data=ApplicationStudentResponse(**application.model_dump()).model_dump(mode="json"),
        message="Application submitted successfully",
    )
