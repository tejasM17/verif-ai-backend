from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_current_student
from app.core.response import success_response
from app.models.student import Student
from app.schemas.company import (
    CompanyResponse,
    CompanyDetailResponse,
)
from app.schemas.job_posting import JobPostingResponse
from app.services.company_profile import CompanyProfileService

router = APIRouter(prefix="/companies", tags=["Companies"])


@router.get("")
async def list_companies(
    tech_stack: str = Query(None, description="Filter by tech stack (comma-separated)"),
    skills: str = Query(None, description="Filter by required skills (comma-separated)"),
    hiring_status: str = Query(None, regex="^(hiring|not_hiring|paused)$"),
    has_internships: bool = Query(None),
    search: str = Query(None, max_length=255),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    student: Student = Depends(get_current_student),
):
    service = CompanyProfileService()
    companies, total = await service.list_companies(
        page=page,
        page_size=page_size,
        tech_stack=tech_stack,
        skills=skills,
        hiring_status=hiring_status,
        has_internships=has_internships,
        search=search,
    )
    return success_response(
        data={
            "companies": [CompanyResponse(**c.model_dump()).model_dump(mode="json") for c in companies],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
        message="Companies retrieved successfully",
    )


@router.get("/{company_id}")
async def get_company_detail(
    company_id: str,
    student: Student = Depends(get_current_student),
):
    service = CompanyProfileService()
    company, postings = await service.get_company_detail(company_id)
    company_data = CompanyResponse(**company.model_dump()).model_dump(mode="json")
    company_data["open_postings"] = [
        JobPostingResponse(**p.model_dump()).model_dump(mode="json") for p in postings
    ]
    return success_response(
        data=company_data,
        message="Company details retrieved successfully",
    )
