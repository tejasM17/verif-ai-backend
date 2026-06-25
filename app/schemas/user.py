from typing import Optional

from pydantic import BaseModel

from app.domain.enums.role import UserRole
from app.schemas.recruiter import RecruiterProfile
from app.schemas.student import StudentProfile


class RoleUpdate(BaseModel):
    role: UserRole


class OnboardingRequest(BaseModel):
    role: UserRole

    student: Optional[StudentProfile] = None
    recruiter: Optional[RecruiterProfile] = None
