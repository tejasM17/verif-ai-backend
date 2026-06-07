from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CompanyProfile(BaseModel):
    id: str
    recruiter_id: str
    firebase_uid: str
    company_name: str
    logo_url: Optional[str] = None
    hiring_status: str = "not_hiring"
    has_internships: bool = False
    tech_stack: list = []
    required_skills: list = []
    location: Optional[str] = None
    summary: Optional[str] = None
    company_website: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
