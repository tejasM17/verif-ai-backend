from pydantic import BaseModel, Field
from typing import Optional


class StudentRegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    password: Optional[str] = Field(None, min_length=6, max_length=128)
    firebase_token: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=20)
    profile_image: Optional[str] = None
    college_name: Optional[str] = Field(None, max_length=255)
    branch: Optional[str] = Field(None, max_length=255)
    graduation_year: Optional[int] = None
    skills: Optional[str] = None
    resume_url: Optional[str] = None


class RecruiterRegisterRequest(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=255)
    recruiter_name: str = Field(..., min_length=1, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    password: Optional[str] = Field(None, min_length=6, max_length=128)
    firebase_token: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=20)
    company_website: Optional[str] = Field(None, max_length=255)
    company_logo: Optional[str] = None
    designation: Optional[str] = Field(None, max_length=255)


class LoginRequest(BaseModel):
    email: Optional[str] = Field(None, max_length=255)
    password: Optional[str] = Field(None, min_length=1, max_length=128)
    firebase_token: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str = ""


class LogoutRequest(BaseModel):
    refresh_token: str = ""
