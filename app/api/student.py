from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_student
from app.core.response import success_response
from app.models.student import Student
from app.schemas.student import StudentResponse, StudentUpdateRequest
from app.services.student import StudentService

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
