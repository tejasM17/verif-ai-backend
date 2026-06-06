from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class RecruiterResponse(BaseModel):
    id: str
    firebase_uid: str
    company_name: str
    recruiter_name: str
    email: str
    phone: Optional[str] = None
    company_website: Optional[str] = None
    company_logo: Optional[str] = None
    designation: Optional[str] = None
    role: str
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class RecruiterUpdateRequest(BaseModel):
    company_name: Optional[str] = Field(None, min_length=1, max_length=255)
    recruiter_name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    company_website: Optional[str] = Field(None, max_length=255)
    company_logo: Optional[str] = None
    designation: Optional[str] = Field(None, max_length=255)
