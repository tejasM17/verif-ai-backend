from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_current_user, require_recruiter
from app.schemas.job import JobCreate, JobListResponse, JobPublic, JobUpdate
from app.services.job_service import JobService


router = APIRouter(tags=["jobs"])
service = JobService()


@router.get("/companies/{company_uid}/jobs", response_model=JobListResponse)
async def list_company_jobs(
    company_uid: str,
    status: str | None = Query(default="open"),
    limit: int = Query(default=50, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
):
    items, total = await service.list_for_company(company_uid, status, limit, skip)
    return {"items": items, "total": total, "limit": limit, "skip": skip}


@router.get("/jobs/{uid}", response_model=JobPublic)
async def get_job(uid: str):
    return await service.get_job(uid)


@router.post("/companies/me/jobs", response_model=JobPublic)
async def create_my_job(
    payload: JobCreate,
    current_user: dict = Depends(require_recruiter),
):
    return await service.create_for_my_company(
        current_user["uid"], current_user["uid"], payload.model_dump()
    )


@router.get("/companies/me/jobs", response_model=JobListResponse)
async def list_my_jobs(
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
    current_user: dict = Depends(require_recruiter),
):
    items, total = await service.list_for_recruiter(
        current_user["uid"], status, limit, skip
    )
    return {"items": items, "total": total, "limit": limit, "skip": skip}


@router.patch("/jobs/{uid}", response_model=JobPublic)
async def update_job(
    uid: str,
    payload: JobUpdate,
    current_user: dict = Depends(require_recruiter),
):
    filtered = payload.model_dump(exclude_unset=True)
    return await service.update_job(current_user["uid"], uid, filtered)


@router.delete("/jobs/{uid}")
async def delete_job(
    uid: str,
    current_user: dict = Depends(require_recruiter),
):
    await service.delete_job(current_user["uid"], uid)
    return {"detail": "Job deleted"}