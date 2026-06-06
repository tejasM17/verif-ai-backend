from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_current_user
from app.core.response import success_response
from app.repositories.student import StudentRepository
from app.repositories.recruiter import RecruiterRepository
from app.schemas.student import StudentResponse
from app.schemas.recruiter import RecruiterResponse

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users")
async def get_all_users(
    current_user: dict = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    student_repo = StudentRepository()
    recruiter_repo = RecruiterRepository()
    students = await student_repo.get_all(skip=skip, limit=limit)
    recruiters = await recruiter_repo.get_all(skip=skip, limit=limit)
    return success_response(
        data={
            "students": [StudentResponse(**s).model_dump() for s in students],
            "recruiters": [RecruiterResponse(**r).model_dump() for r in recruiters],
            "total_students": len(students),
            "total_recruiters": len(recruiters),
        },
        message="All users retrieved",
    )


@router.get("/students")
async def get_all_students(
    current_user: dict = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    repo = StudentRepository()
    students = await repo.get_all(skip=skip, limit=limit)
    return success_response(
        data=[StudentResponse(**s).model_dump() for s in students],
        message="All students retrieved",
    )


@router.get("/recruiters")
async def get_all_recruiters(
    current_user: dict = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    repo = RecruiterRepository()
    recruiters = await repo.get_all(skip=skip, limit=limit)
    return success_response(
        data=[RecruiterResponse(**r).model_dump() for r in recruiters],
        message="All recruiters retrieved",
    )


@router.patch("/user/status")
async def update_user_status(
    user_id: str,
    role: str,
    is_active: bool,
    current_user: dict = Depends(get_current_user),
):
    if role == "student":
        repo = StudentRepository()
    elif role == "recruiter":
        repo = RecruiterRepository()
    else:
        return success_response(message="Invalid role specified", status_code=400)

    success = await repo.update(user_id, is_active=is_active)
    if not success:
        return success_response(message="User not found", status_code=404)
    return success_response(
        data={"is_active": is_active},
        message=f"User {'activated' if is_active else 'deactivated'} successfully",
    )
