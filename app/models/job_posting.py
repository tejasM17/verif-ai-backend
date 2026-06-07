from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class JobOrInternshipPosting(BaseModel):
    id: str
    company_id: str
    recruiter_id: str
    firebase_uid: str
    title: str
    type: str
    description: str
    requirements: list = []
    location: Optional[str] = None
    is_remote: bool = False
    stipend_salary: Optional[str] = None
    duration: Optional[str] = None
    status: str = "open"
    application_deadline: Optional[datetime] = None
    tech_stack: list = []
    skills_required: list = []
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
