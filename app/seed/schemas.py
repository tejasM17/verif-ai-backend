from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SeedDoc(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    _id: str

    def to_mongo(self) -> dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=False)


class CountryDoc(SeedDoc):
    name: str
    code: str = Field(min_length=2, max_length=2)
    code3: str = Field(min_length=3, max_length=3)
    dial_code: str
    currency: str
    currency_symbol: str
    locale: str
    default_timezone: str
    languages: list[str]
    primary_language: str

    @field_validator("code")
    @classmethod
    def _upper_code(cls, v: str) -> str:
        return v.upper()

    @field_validator("code3")
    @classmethod
    def _upper_code3(cls, v: str) -> str:
        return v.upper()


class StateDoc(SeedDoc):
    name: str
    code: str
    country_code: str
    country_name: str

    @field_validator("country_code")
    @classmethod
    def _upper_country(cls, v: str) -> str:
        return v.upper()


class CityDoc(SeedDoc):
    name: str
    country_code: str
    country_name: str
    state_code: str
    state_name: str
    latitude: float
    longitude: float
    timezone: str
    population: Optional[int] = None
    is_major: bool = False

    @field_validator("country_code")
    @classmethod
    def _upper_country(cls, v: str) -> str:
        return v.upper()


class SkillDoc(SeedDoc):
    name: str
    slug: str
    category: str
    subcategory: Optional[str] = None
    demand_score: float = Field(ge=0.0, le=1.0)
    related_skills: list[str] = Field(default_factory=list)


class JobCategoryDoc(SeedDoc):
    name: str
    slug: str
    description: str
    display_order: int = 0
    is_active: bool = True


class DepartmentDoc(SeedDoc):
    name: str
    slug: str
    display_order: int = 0
    is_active: bool = True


class EmploymentTypeDoc(SeedDoc):
    name: str
    slug: str
    display_order: int = 0
    is_active: bool = True


class ExperienceLevelDoc(SeedDoc):
    name: str
    slug: str
    min_years: int = 0
    max_years: int = 0
    display_order: int = 0
    is_active: bool = True


class CompanyDoc(SeedDoc):
    name: str
    slug: str
    description: str
    industry: str
    sub_industry: Optional[str] = None
    founded_year: int = Field(ge=1900, le=2030)
    company_size: str
    headquarters_city: str
    headquarters_state: Optional[str] = None
    headquarters_country: str
    country_code: str
    hq_city_id: Optional[str] = None
    hq_state_id: Optional[str] = None
    hq_country_id: Optional[str] = None
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    github_url: Optional[str] = None
    logo_url: str
    cover_image_url: str
    culture: str
    benefits: list[str] = Field(default_factory=list)
    tech_stack: list[str] = Field(default_factory=list)
    hiring_status: str
    verification_status: str
    rating: float = Field(ge=0.0, le=5.0)
    review_count: int = 0
    social_links: dict = Field(default_factory=dict)
    active_recruiters: int = 0
    active_jobs: int = 0
    tags: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class RecruiterDoc(SeedDoc):
    email: str
    firebase_uid: Optional[str] = None
    firebase_sync_status: str = "pending"
    display_name: str
    photo_url: str
    company_id: str
    company_slug: str
    designation: str
    bio: str
    years_experience: int = Field(ge=0, le=50)
    specialties: list[str]
    preferred_technologies: list[str]
    languages: list[str]
    timezone: str
    country: str
    country_code: str
    state: Optional[str] = None
    state_code: Optional[str] = None
    city: str
    city_id: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    verification_badge: bool = False
    active_status: bool = True
    online_status: bool = False
    last_login: datetime
    created_at: datetime
    updated_at: datetime


class RecruiterProfileDoc(SeedDoc):
    recruiter_id: str
    company_id: str
    headline: str
    about: str
    skills: list[str]
    experience: list[dict]
    education: list[dict]
    certifications: list[dict]
    social_links: dict = Field(default_factory=dict)
    languages: list[dict]
    preferences: dict = Field(default_factory=dict)


class RecruiterPreferencesDoc(SeedDoc):
    recruiter_id: str
    job_alerts: bool = True
    email_notifications: bool = True
    push_notifications: bool = True
    sms_notifications: bool = False
    weekly_digest: bool = True
    preferred_job_types: list[str]
    preferred_locations: list[str]
    preferred_remote: list[str]
    min_salary: Optional[int] = None
    max_salary: Optional[int] = None
    preferred_industries: list[str]
    updated_at: datetime


class RecruiterVerificationDoc(SeedDoc):
    recruiter_id: str
    status: str
    email_verified: bool = False
    phone_verified: bool = False
    identity_verified: bool = False
    company_verified: bool = False
    background_check: bool = False
    verified_at: Optional[datetime] = None
    verification_score: float = 0.0
    documents: list[dict] = Field(default_factory=list)


class RecruiterNotificationDoc(SeedDoc):
    recruiter_id: str
    type: str
    title: str
    message: str
    read: bool = False
    action_url: Optional[str] = None
    created_at: datetime
    read_at: Optional[datetime] = None


class RecruiterSessionDoc(SeedDoc):
    session_token: str
    recruiter_id: str
    ip_address: str
    user_agent: str
    device: str
    location: Optional[str] = None
    active: bool = True
    created_at: datetime
    last_active: datetime
    expires_at: datetime


class RecruiterActivityDoc(SeedDoc):
    recruiter_id: str
    activity_type: str
    description: str
    metadata: dict = Field(default_factory=dict)
    ip_address: Optional[str] = None
    created_at: datetime


class JobDoc(SeedDoc):
    title: str
    description: str
    responsibilities: list[str]
    requirements: list[str]
    nice_to_have: list[str] = Field(default_factory=list)
    salary_min: int = Field(ge=0)
    salary_max: int = Field(ge=0)
    currency: str
    salary_period: str = "yearly"
    experience_min: int = Field(ge=0)
    experience_max: int = Field(ge=0)
    education: str
    work_mode: str
    employment_type: str
    experience_level: str
    department: str
    category: str
    company_id: str
    company_slug: str
    company_name: str
    recruiter_id: str
    location_city: str
    location_state: Optional[str] = None
    location_country: str
    location_country_code: str
    city_id: Optional[str] = None
    remote: bool = False
    openings: int = 1
    application_deadline: Optional[datetime] = None
    benefits: list[str]
    required_skills: list[str]
    preferred_skills: list[str]
    tags: list[str] = Field(default_factory=list)
    status: str
    applicants_count: int = 0
    views_count: int = 0
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def _validate_ranges(self) -> "JobDoc":
        if self.salary_max < self.salary_min:
            raise ValueError("salary_max must be >= salary_min")
        if self.experience_max < self.experience_min:
            raise ValueError("experience_max must be >= experience_min")
        return self


__all__ = [
    "CountryDoc", "StateDoc", "CityDoc", "SkillDoc",
    "JobCategoryDoc", "DepartmentDoc", "EmploymentTypeDoc", "ExperienceLevelDoc",
    "CompanyDoc", "RecruiterDoc", "RecruiterProfileDoc", "RecruiterPreferencesDoc",
    "RecruiterVerificationDoc", "RecruiterNotificationDoc", "RecruiterSessionDoc",
    "RecruiterActivityDoc", "JobDoc",
]
