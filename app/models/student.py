from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Student(BaseModel):
    id: str
    firebase_uid: str
    full_name: str
    email: str
    phone: Optional[str] = None
    profile_image: Optional[str] = None
    college_name: Optional[str] = None
    branch: Optional[str] = None
    graduation_year: Optional[int] = None
    skills: Optional[str] = None
    resume_url: Optional[str] = None
    role: str = "student"
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
