from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_current_user, require_recruiter
from app.schemas.company import (
    CompanyCreate,
    CompanyPublic,
    CompanySearchResult,
    CompanyUpdate,
)
from app.services.company_service import CompanyService


router = APIRouter(prefix="/companies", tags=["companies"])
service = CompanyService()


def _clamp_limit(limit: int) -> int:
    return max(1, min(limit, 100))


def _clamp_skip(skip: int) -> int:
    return max(0, skip)


@router.post("/me", response_model=CompanyPublic)
def upsert_my_company(
    payload: CompanyCreate,
    current_user: dict = Depends(require_recruiter),
):
    return service.create_or_update_my_company(current_user["uid"], payload)


@router.get("/me", response_model=CompanyPublic)
def get_my_company(current_user: dict = Depends(require_recruiter)):
    return service.get_my_company(current_user["uid"])


@router.put("/me", response_model=CompanyPublic)
def update_my_company(
    payload: CompanyUpdate,
    current_user: dict = Depends(require_recruiter),
):
    return service.update_my_company(current_user["uid"], payload)


@router.get("/search", response_model=CompanySearchResult)
def search_companies(
    q: str | None = Query(default=None, description="Free-text query"),
    location: str | None = Query(default=None),
    role: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
):
    items, total = service.search_companies(
        q=q, location=location, role=role, limit=limit, skip=skip
    )
    return {"items": items, "total": total, "limit": limit, "skip": skip}


@router.get("", response_model=CompanySearchResult)
def list_companies(
    limit: int = Query(default=20, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
):
    items, total = service.list_companies(limit=limit, skip=skip)
    return {"items": items, "total": total, "limit": limit, "skip": skip}


@router.get("/{uid}", response_model=CompanyPublic)
def get_company(uid: str):
    return service.get_company_by_uid(uid)