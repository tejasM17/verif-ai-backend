from pydantic import BaseModel, EmailStr
from typing import Optional

from app.domain.enums.role import UserRole


class RecruiterProfile(BaseModel):
    uid: str
    email: EmailStr
    display_name: Optional[str] = None
    photo_url: Optional[str] = None
    role: UserRole = UserRole.recruiter

    company_name: Optional[str] = None
    company_email: Optional[str] = None
