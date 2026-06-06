from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_recruiter
from app.core.response import success_response
from app.models.recruiter import Recruiter
from app.schemas.recruiter import RecruiterResponse, RecruiterUpdateRequest
from app.services.recruiter import RecruiterService

router = APIRouter(prefix="/recruiter", tags=["Recruiter"])


@router.get("/me")
async def get_current_recruiter_info(recruiter: Recruiter = Depends(get_current_recruiter)):
    return success_response(
        data=RecruiterResponse(**recruiter.model_dump()).model_dump(mode="json"),
        message="Recruiter profile retrieved",
    )


@router.get("/profile")
async def get_recruiter_profile(recruiter: Recruiter = Depends(get_current_recruiter)):
    return success_response(
        data=RecruiterResponse(**recruiter.model_dump()).model_dump(mode="json"),
        message="Recruiter profile retrieved",
    )


@router.put("/profile")
async def update_recruiter_profile(
    request: RecruiterUpdateRequest,
    recruiter: Recruiter = Depends(get_current_recruiter),
):
    service = RecruiterService()
    updated = await service.update_profile(
        recruiter=recruiter,
        **request.model_dump(exclude_none=True),
    )
    return success_response(
        data=RecruiterResponse(**updated.model_dump()).model_dump(mode="json"),
        message="Profile updated successfully",
    )


@router.delete("/profile")
async def delete_recruiter_profile(recruiter: Recruiter = Depends(get_current_recruiter)):
    service = RecruiterService()
    await service.delete_profile(recruiter)
    return success_response(message="Profile deleted successfully")
