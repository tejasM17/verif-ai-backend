from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class StudentResponse(BaseModel):
    id: str
    firebase_uid: str
    full_name: str
    email: str
    phone: Optional[str] = None
    profile_image: Optional[str] = None
    profile_photo_url: Optional[str] = None
    college_name: Optional[str] = None
    branch: Optional[str] = None
    graduation_year: Optional[int] = None
    skills: Optional[str] = None
    resume_url: Optional[str] = None
    role: str
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class StudentUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    profile_image: Optional[str] = None
    profile_photo_url: Optional[str] = None
    college_name: Optional[str] = Field(None, max_length=255)
    branch: Optional[str] = Field(None, max_length=255)
    graduation_year: Optional[int] = None
    skills: Optional[str] = None
    resume_url: Optional[str] = None
