from pydantic import BaseModel, EmailStr
from typing import Optional
from app.domain.enums.role import UserRole


class StudentProfile(BaseModel):
    uid: str
    email: EmailStr
    display_name: Optional[str] = None
    photo_url: Optional[str] = None
    resume_url: Optional[str] = None
    role: UserRole = UserRole.student
    skills: list[str] = []


class RecruiterProfile(BaseModel):
    uid: str
    email: EmailStr
    display_name: Optional[str] = None
    photo_url: Optional[str] = None
    role: UserRole = UserRole.recruiter

    company_name: Optional[str] = None
    company_email: Optional[str] = None


class RoleUpdate(BaseModel):
    role: UserRole


class OnboardingRequest(BaseModel):
    role: UserRole

    student: Optional[StudentProfile] = None
    recruiter: Optional[RecruiterProfile] = None
