from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class JobPostingCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    type: str = Field(..., pattern=r"^(job|internship)$")
    description: str = Field(..., min_length=1, max_length=5000)
    requirements: list[str] = []
    location: Optional[str] = Field(None, max_length=255)
    is_remote: bool = False
    stipend_salary: Optional[str] = Field(None, max_length=255)
    duration: Optional[str] = Field(None, max_length=255)
    application_deadline: Optional[datetime] = None
    tech_stack: list[str] = []
    skills_required: list[str] = []


class JobPostingUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1, max_length=5000)
    requirements: Optional[list[str]] = None
    location: Optional[str] = Field(None, max_length=255)
    is_remote: Optional[bool] = None
    stipend_salary: Optional[str] = Field(None, max_length=255)
    duration: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = Field(None, pattern=r"^(open|closed|filled)$")
    application_deadline: Optional[datetime] = None
    tech_stack: Optional[list[str]] = None
    skills_required: Optional[list[str]] = None


class JobPostingResponse(BaseModel):
    id: str
    company_id: str
    recruiter_id: str
    title: str
    type: str
    description: str
    requirements: list
    location: Optional[str] = None
    is_remote: bool
    stipend_salary: Optional[str] = None
    duration: Optional[str] = None
    status: str
    application_deadline: Optional[datetime] = None
    tech_stack: list
    skills_required: list
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
