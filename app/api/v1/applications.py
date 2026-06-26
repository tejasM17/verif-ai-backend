from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_current_user, require_recruiter, require_student
from app.schemas.application import (
    ApplicationListResponse,
    ApplicationPublic,
    ApplicationStatus,
    ApplicationStatusUpdate,
    ApplicationSubmit,
)
from app.services.application_service import ApplicationService


router = APIRouter(prefix="/applications", tags=["applications"])
service = ApplicationService()


@router.post("/submit", response_model=ApplicationPublic)
def submit_application(
    payload: ApplicationSubmit,
    current_user: dict = Depends(require_student),
):
    return service.submit(current_user["uid"], payload)


@router.get("/me", response_model=ApplicationListResponse)
def my_applications(
    limit: int = Query(default=20, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
    current_user: dict = Depends(require_student),
):
    items, total = service.list_for_student(current_user["uid"], limit, skip)
    return {"items": items, "total": total, "limit": limit, "skip": skip}


@router.get("/recruiter/me", response_model=ApplicationListResponse)
def recruiter_applications(
    status: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
    current_user: dict = Depends(require_recruiter),
):
    items, total = service.list_for_recruiter(
        current_user["uid"], status, limit, skip
    )
    return {"items": items, "total": total, "limit": limit, "skip": skip}


@router.get("/{app_id}", response_model=ApplicationPublic)
def get_application(
    app_id: str,
    current_user: dict = Depends(get_current_user),
):
    return service.get_for_student_or_recruiter(
        app_id, current_user["uid"], current_user.get("role") or ""
    )


@router.patch("/{app_id}/status", response_model=ApplicationPublic)
def update_application_status(
    app_id: str,
    payload: ApplicationStatusUpdate,
    current_user: dict = Depends(require_recruiter),
):
    return service.update_status(
        recruiter_uid=current_user["uid"],
        app_id=app_id,
        new_status=payload.status,
        note=payload.note,
    )


@router.delete("/{app_id}")
def delete_application(
    app_id: str,
    current_user: dict = Depends(require_student),
):
    service.delete_for_student(current_user["uid"], app_id)
    return {"detail": "Application deleted"}