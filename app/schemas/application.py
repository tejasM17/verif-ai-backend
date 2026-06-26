from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ApplicationStatus(str, Enum):
    submitted = "submitted"
    reviewing = "reviewing"
    accepted = "accepted"
    rejected = "rejected"


class ApplicationSubmit(BaseModel):
    resume_uid: str = Field(..., min_length=1)
    company_uid: str = Field(..., min_length=1)
    why_appoint: str = Field(..., min_length=1, max_length=4000)
    job_uid: Optional[str] = Field(default=None, max_length=64)


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus
    note: Optional[str] = Field(default=None, max_length=1000)


class StatusHistoryEntry(BaseModel):
    status: ApplicationStatus
    changed_at: datetime
    note: Optional[str] = None


class ApplicationPublic(BaseModel):
    id: str
    student_uid: str
    recruiter_uid: str
    company_uid: str
    resume_uid: str
    why_appoint: str
    status: ApplicationStatus
    status_history: list[StatusHistoryEntry] = []
    created_at: datetime
    updated_at: datetime


class ApplicationListItem(BaseModel):
    id: str
    company_uid: str
    company_name: Optional[str] = None
    company_role: Optional[str] = None
    company_location: Optional[str] = None
    company_logo_url: Optional[str] = None
    job_uid: Optional[str] = None
    job_title: Optional[str] = None
    student_uid: Optional[str] = None
    student_display_name: Optional[str] = None
    student_email: Optional[str] = None
    student_photo_url: Optional[str] = None
    student_skills: list[str] = []
    resume_uid: str
    resume_url: Optional[str] = None
    why_appoint: str
    status: ApplicationStatus
    created_at: datetime
    updated_at: datetime


class ApplicationListResponse(BaseModel):
    items: list[ApplicationListItem]
    total: int
    limit: int
    skip: int