from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ApplicationStatusHistory(BaseModel):
    status: str
    changed_by: str
    changed_by_role: str
    reason: Optional[str] = None
    timestamp: Optional[datetime] = None


class Application(BaseModel):
    id: str
    student_id: str
    student_firebase_uid: str
    company_id: str
    posting_id: str
    resume_file_id: Optional[str] = None
    certificate_file_id: Optional[str] = None
    github_project_link: str = ""
    cover_letter: Optional[str] = None
    status: str = "draft"
    status_history: list = []
    is_active: bool = True
    submitted_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
