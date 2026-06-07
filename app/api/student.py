from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_current_student
from app.core.response import success_response
from app.core.exceptions import NotFoundException
from app.models.student import Student
from app.schemas.student import StudentResponse, StudentUpdateRequest
from app.schemas.application import ApplicationStudentResponse
from app.services.student import StudentService
from app.services.application import ApplicationService
from app.services.student_saved_company import StudentSavedCompanyService
from app.repositories.student import StudentRepository

router = APIRouter(prefix="/student", tags=["Student"])

PHOTO_URL = "/student/profile/photo"


def _inject_photo_url(student: Student) -> dict:
    data = StudentResponse(**student.model_dump()).model_dump(mode="json")
    data["profile_photo_url"] = PHOTO_URL
    return data


@router.get("/me")
async def get_current_student_info(student: Student = Depends(get_current_student)):
    return success_response(
        data=_inject_photo_url(student),
        message="Student profile retrieved",
    )


@router.get("/profile")
async def get_student_profile(student: Student = Depends(get_current_student)):
    return success_response(
        data=_inject_photo_url(student),
        message="Student profile retrieved",
    )


@router.put("/profile")
async def update_student_profile(
    request: StudentUpdateRequest,
    student: Student = Depends(get_current_student),
):
    service = StudentService()
    updated = await service.update_profile(
        student=student,
        **request.model_dump(exclude_none=True),
    )
    return success_response(
        data=_inject_photo_url(updated),
        message="Profile updated successfully",
    )


@router.delete("/profile")
async def delete_student_profile(student: Student = Depends(get_current_student)):
    service = StudentService()
    await service.delete_profile(student)
    return success_response(message="Profile deleted successfully")


@router.get("/applications")
async def list_student_applications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    student: Student = Depends(get_current_student),
):
    service = ApplicationService()
    applications, total = await service.list_student_applications(
        student_id=student.id,
        page=page,
        page_size=page_size,
    )
    return success_response(
        data={
            "applications": [
                ApplicationStudentResponse(**app.model_dump()).model_dump(mode="json")
                for app in applications
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
        message="Applications retrieved successfully",
    )


@router.get("/applications/{application_id}")
async def get_student_application(
    application_id: str,
    student: Student = Depends(get_current_student),
):
    service = ApplicationService()
    application = await service.get_student_application(application_id, student.id)
    return success_response(
        data=ApplicationStudentResponse(**application.model_dump()).model_dump(mode="json"),
        message="Application retrieved successfully",
    )


@router.post("/saved-companies")
async def save_company(
    company_id: str = Query(..., min_length=1),
    student: Student = Depends(get_current_student),
):
    service = StudentSavedCompanyService()
    saved = await service.save_company(student.id, student.firebase_uid, company_id)
    return success_response(
        data=saved.model_dump(mode="json"),
        message="Company saved successfully",
        status_code=201,
    )


@router.get("/saved-companies")
async def list_saved_companies(
    student: Student = Depends(get_current_student),
):
    service = StudentSavedCompanyService()
    saved_list = await service.list_saved_companies(student.id)
    return success_response(
        data={
            "saved_companies": [s.model_dump(mode="json") for s in saved_list],
            "total": len(saved_list),
        },
        message="Saved companies retrieved successfully",
    )


@router.delete("/saved-companies/{company_id}")
async def remove_saved_company(
    company_id: str,
    student: Student = Depends(get_current_student),
):
    service = StudentSavedCompanyService()
    await service.unsave_company(student.id, company_id)
    return success_response(message="Company removed from saved list")
