from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Recruiter(BaseModel):
    id: str
    firebase_uid: str
    company_name: str
    recruiter_name: str
    email: str
    phone: Optional[str] = None
    company_website: Optional[str] = None
    company_logo: Optional[str] = None
    designation: Optional[str] = None
    role: str = "recruiter"
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
