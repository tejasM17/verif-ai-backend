from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class JobCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    department: Optional[str] = Field(default=None, max_length=100)
    location: Optional[str] = Field(default=None, max_length=200)
    employment_type: Optional[str] = Field(default=None, max_length=50)  # full-time / part-time / contract / intern
    work_mode: Optional[str] = Field(default=None, max_length=50)  # remote / hybrid / on-site
    experience_level: Optional[str] = Field(default=None, max_length=50)  # entry / mid / senior / lead
    description: Optional[str] = Field(default=None, max_length=4000)
    required_skills: list[str] = Field(default_factory=list)
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    currency: Optional[str] = Field(default=None, max_length=10)


class JobUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    department: Optional[str] = Field(default=None, max_length=100)
    location: Optional[str] = Field(default=None, max_length=200)
    employment_type: Optional[str] = Field(default=None, max_length=50)
    work_mode: Optional[str] = Field(default=None, max_length=50)
    experience_level: Optional[str] = Field(default=None, max_length=50)
    description: Optional[str] = Field(default=None, max_length=4000)
    required_skills: Optional[list[str]] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    currency: Optional[str] = Field(default=None, max_length=10)
    status: Optional[str] = Field(default=None, max_length=20)  # open / closed


class JobPublic(BaseModel):
    uid: str
    company_uid: str
    company_name: Optional[str] = None
    company_logo_url: Optional[str] = None
    title: str
    department: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    work_mode: Optional[str] = None
    experience_level: Optional[str] = None
    description: Optional[str] = None
    required_skills: list[str] = []
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    currency: Optional[str] = None
    status: str = "open"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class JobListResponse(BaseModel):
    items: list[JobPublic]
    total: int
    limit: int
    skip: int
