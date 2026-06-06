from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class StudentRegisterRequest(BaseModel):
    firebase_token: str = Field(..., description="Firebase ID token")
    full_name: str = Field(..., min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    profile_image: Optional[str] = None
    college_name: Optional[str] = Field(None, max_length=255)
    branch: Optional[str] = Field(None, max_length=255)
    graduation_year: Optional[int] = None
    skills: Optional[str] = None
    resume_url: Optional[str] = None


class RecruiterRegisterRequest(BaseModel):
    firebase_token: str = Field(..., description="Firebase ID token")
    company_name: str = Field(..., min_length=1, max_length=255)
    recruiter_name: str = Field(..., min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    company_website: Optional[str] = Field(None, max_length=255)
    company_logo: Optional[str] = None
    designation: Optional[str] = Field(None, max_length=255)


class LoginRequest(BaseModel):
    firebase_token: str = Field(..., description="Firebase ID token from frontend")


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class LogoutRequest(BaseModel):
    refresh_token: str
