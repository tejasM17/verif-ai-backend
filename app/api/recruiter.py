from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_current_recruiter
from app.core.response import success_response
from app.models.recruiter import Recruiter
from app.schemas.recruiter import RecruiterResponse, RecruiterUpdateRequest
from app.schemas.company import CompanyCreateRequest, CompanyUpdateRequest, CompanyResponse
from app.schemas.job_posting import (
    JobPostingCreateRequest,
    JobPostingUpdateRequest,
    JobPostingResponse,
)
from app.schemas.application import (
    ApplicationStatusUpdateRequest,
    ApplicationRecruiterResponse,
)
from app.services.recruiter import RecruiterService
from app.services.company_profile import CompanyProfileService
from app.services.job_posting import JobPostingService
from app.services.application import ApplicationService
from app.repositories.student import StudentRepository

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


@router.post("/companies")
async def create_company(
    request: CompanyCreateRequest,
    recruiter: Recruiter = Depends(get_current_recruiter),
):
    service = CompanyProfileService()
    company = await service.create_company(
        recruiter_id=recruiter.id,
        firebase_uid=recruiter.firebase_uid,
        **request.model_dump(),
    )
    return success_response(
        data=CompanyResponse(**company.model_dump()).model_dump(mode="json"),
        message="Company profile created successfully",
        status_code=201,
    )


@router.get("/companies")
async def get_my_company(
    recruiter: Recruiter = Depends(get_current_recruiter),
):
    service = CompanyProfileService()
    company = await service.get_company_by_firebase_uid(recruiter.firebase_uid)
    if not company:
        return success_response(
            data=None,
            message="No company profile found",
        )
    return success_response(
        data=CompanyResponse(**company.model_dump()).model_dump(mode="json"),
        message="Company profile retrieved",
    )


@router.put("/companies/{company_id}")
async def update_company(
    company_id: str,
    request: CompanyUpdateRequest,
    recruiter: Recruiter = Depends(get_current_recruiter),
):
    service = CompanyProfileService()
    company = await service.update_company(
        company_id=company_id,
        firebase_uid=recruiter.firebase_uid,
        **request.model_dump(exclude_none=True),
    )
    return success_response(
        data=CompanyResponse(**company.model_dump()).model_dump(mode="json"),
        message="Company profile updated successfully",
    )


@router.post("/postings")
async def create_posting(
    request: JobPostingCreateRequest,
    recruiter: Recruiter = Depends(get_current_recruiter),
):
    company_service = CompanyProfileService()
    company = await company_service.get_company_by_firebase_uid(recruiter.firebase_uid)
    if not company:
        from app.core.exceptions import NotFoundException
        raise NotFoundException(
            "Create a company profile first",
            error_code="COMPANY_NOT_FOUND",
        )

    posting_service = JobPostingService()
    posting = await posting_service.create_posting(
        company_id=company.id,
        recruiter_id=recruiter.id,
        firebase_uid=recruiter.firebase_uid,
        **request.model_dump(),
    )
    return success_response(
        data=JobPostingResponse(**posting.model_dump()).model_dump(mode="json"),
        message="Job posting created successfully",
        status_code=201,
    )


@router.get("/postings")
async def list_my_postings(
    recruiter: Recruiter = Depends(get_current_recruiter),
):
    posting_service = JobPostingService()
    postings = await posting_service.list_by_recruiter(recruiter.id)
    return success_response(
        data={
            "postings": [
                JobPostingResponse(**p.model_dump()).model_dump(mode="json") for p in postings
            ],
            "total": len(postings),
        },
        message="Postings retrieved successfully",
    )


@router.put("/postings/{posting_id}")
async def update_posting(
    posting_id: str,
    request: JobPostingUpdateRequest,
    recruiter: Recruiter = Depends(get_current_recruiter),
):
    posting_service = JobPostingService()
    posting = await posting_service.update_posting(
        posting_id=posting_id,
        firebase_uid=recruiter.firebase_uid,
        **request.model_dump(exclude_none=True),
    )
    return success_response(
        data=JobPostingResponse(**posting.model_dump()).model_dump(mode="json"),
        message="Job posting updated successfully",
    )


@router.delete("/postings/{posting_id}")
async def delete_posting(
    posting_id: str,
    recruiter: Recruiter = Depends(get_current_recruiter),
):
    posting_service = JobPostingService()
    await posting_service.delete_posting(posting_id, recruiter.firebase_uid)
    return success_response(message="Job posting deleted successfully")


@router.get("/applications")
async def list_recruiter_applications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    recruiter: Recruiter = Depends(get_current_recruiter),
):
    service = ApplicationService()
    applications, total, company = await service.list_recruiter_applications(
        firebase_uid=recruiter.firebase_uid,
        page=page,
        page_size=page_size,
    )
    result = []
    student_repo = StudentRepository()
    for app in applications:
        student_data = await student_repo.get(app.student_id)
        posting_data = None
        try:
            from app.repositories.job_posting import JobPostingRepository
            posting_repo = JobPostingRepository()
            posting_data = await posting_repo.get(app.posting_id)
        except Exception:
            pass

        app_dict = ApplicationRecruiterResponse(
            id=app.id,
            student_id=app.student_id,
            student_name=student_data.full_name if student_data else "Unknown",
            student_email=student_data.email if student_data else "",
            college_name=student_data.college_name if student_data else None,
            posting_id=app.posting_id,
            posting_title=posting_data.get("title", "Unknown") if posting_data else "Unknown",
            resume_file_id=app.resume_file_id,
            certificate_file_id=app.certificate_file_id,
            github_project_link=app.github_project_link,
            cover_letter=app.cover_letter,
            status=app.status,
            status_history=app.status_history,
            created_at=app.created_at,
            updated_at=app.updated_at,
        ).model_dump(mode="json")
        result.append(app_dict)

    return success_response(
        data={
            "applications": result,
            "total": total,
            "page": page,
            "page_size": page_size,
        },
        message="Applications retrieved successfully",
    )


@router.get("/applications/{application_id}")
async def get_recruiter_application(
    application_id: str,
    recruiter: Recruiter = Depends(get_current_recruiter),
):
    service = ApplicationService()
    app, student, posting = await service.get_recruiter_application(
        application_id,
        recruiter.firebase_uid,
    )
    resp = ApplicationRecruiterResponse(
        id=app.id,
        student_id=app.student_id,
        student_name=student.full_name if student else "Unknown",
        student_email=student.email if student else "",
        college_name=student.college_name if student else None,
        posting_id=app.posting_id,
        posting_title=posting.title if posting else "Unknown",
        resume_file_id=app.resume_file_id,
        certificate_file_id=app.certificate_file_id,
        github_project_link=app.github_project_link,
        cover_letter=app.cover_letter,
        status=app.status,
        status_history=app.status_history,
        created_at=app.created_at,
        updated_at=app.updated_at,
    )
    return success_response(
        data=resp.model_dump(mode="json"),
        message="Application retrieved successfully",
    )


@router.patch("/applications/{application_id}/status")
async def update_application_status(
    application_id: str,
    request: ApplicationStatusUpdateRequest,
    recruiter: Recruiter = Depends(get_current_recruiter),
):
    service = ApplicationService()
    application = await service.update_application_status(
        application_id=application_id,
        firebase_uid=recruiter.firebase_uid,
        new_status=request.status,
        reason=request.reason,
    )
    return success_response(
        data=ApplicationRecruiterResponse(
            id=application.id,
            student_id=application.student_id,
            student_name="",
            posting_id=application.posting_id,
            posting_title="",
            resume_file_id=application.resume_file_id,
            certificate_file_id=application.certificate_file_id,
            github_project_link=application.github_project_link,
            cover_letter=application.cover_letter,
            status=application.status,
            status_history=application.status_history,
            created_at=application.created_at,
            updated_at=application.updated_at,
        ).model_dump(mode="json"),
        message=f"Application status updated to {request.status}",
    )
