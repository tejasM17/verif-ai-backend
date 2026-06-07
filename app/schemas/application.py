from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ApplicationCreateRequest(BaseModel):
    company_id: str = Field(..., min_length=1)
    posting_id: str = Field(..., min_length=1)
    github_project_link: str = Field(..., min_length=1)
    cover_letter: Optional[str] = Field(None, max_length=5000)


class ApplicationSubmitRequest(BaseModel):
    application_id: str = Field(..., min_length=1)


class ApplicationStatusUpdateRequest(BaseModel):
    status: str = Field(..., pattern=r"^(submitted|reviewing|selected|rejected|request_changes)$")
    reason: Optional[str] = Field(None, max_length=1000)


class ApplicationStatusHistoryResponse(BaseModel):
    status: str
    changed_by: str
    changed_by_role: str
    reason: Optional[str] = None
    timestamp: Optional[datetime] = None


class ApplicationStudentResponse(BaseModel):
    id: str
    student_id: str
    company_id: str
    posting_id: str
    resume_file_id: Optional[str] = None
    certificate_file_id: Optional[str] = None
    github_project_link: str = ""
    cover_letter: Optional[str] = None
    status: str
    status_history: list = []
    submitted_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ApplicationRecruiterResponse(BaseModel):
    id: str
    student_id: str
    student_name: str = ""
    student_email: str = ""
    college_name: Optional[str] = None
    posting_id: str
    posting_title: str = ""
    resume_file_id: Optional[str] = None
    certificate_file_id: Optional[str] = None
    github_project_link: str = ""
    cover_letter: Optional[str] = None
    status: str
    status_history: list = []
    submitted_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
