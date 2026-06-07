from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CompanyCreateRequest(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=255)
    logo_url: Optional[str] = None
    hiring_status: str = Field(default="not_hiring", pattern=r"^(hiring|not_hiring|paused)$")
    has_internships: bool = False
    tech_stack: list[str] = []
    required_skills: list[str] = []
    location: Optional[str] = Field(None, max_length=255)
    summary: Optional[str] = Field(None, max_length=2000)
    company_website: Optional[str] = None


class CompanyUpdateRequest(BaseModel):
    company_name: Optional[str] = Field(None, min_length=1, max_length=255)
    logo_url: Optional[str] = None
    hiring_status: Optional[str] = Field(None, pattern=r"^(hiring|not_hiring|paused)$")
    has_internships: Optional[bool] = None
    tech_stack: Optional[list[str]] = None
    required_skills: Optional[list[str]] = None
    location: Optional[str] = Field(None, max_length=255)
    summary: Optional[str] = Field(None, max_length=2000)
    company_website: Optional[str] = None


class CompanyResponse(BaseModel):
    id: str
    recruiter_id: str
    company_name: str
    logo_url: Optional[str] = None
    hiring_status: str
    has_internships: bool
    tech_stack: list
    required_skills: list
    location: Optional[str] = None
    summary: Optional[str] = None
    company_website: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CompanyDetailResponse(CompanyResponse):
    open_postings: list = []


class CompanyListFilterParams(BaseModel):
    tech_stack: Optional[str] = None
    skills: Optional[str] = None
    hiring_status: Optional[str] = Field(None, pattern=r"^(hiring|not_hiring|paused)$")
    has_internships: Optional[bool] = None
    search: Optional[str] = Field(None, max_length=255)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
