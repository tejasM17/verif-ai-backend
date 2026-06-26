from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CompanyCreate(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=200)
    role: str = Field(..., min_length=1, max_length=200)
    location: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=4000)
    website: Optional[str] = Field(default=None, max_length=500)
    industry: Optional[str] = Field(default=None, max_length=200)
    company_size: Optional[str] = Field(default=None, max_length=50)
    logo_url: Optional[str] = Field(default=None, max_length=1000)


class CompanyUpdate(BaseModel):
    company_name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    role: Optional[str] = Field(default=None, min_length=1, max_length=200)
    location: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=4000)
    website: Optional[str] = Field(default=None, max_length=500)
    industry: Optional[str] = Field(default=None, max_length=200)
    company_size: Optional[str] = Field(default=None, max_length=50)
    logo_url: Optional[str] = Field(default=None, max_length=1000)


class CompanyPublic(BaseModel):
    uid: str
    company_name: str
    role: str
    location: str
    description: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    logo_url: Optional[str] = None
    follower_count: int = 0
    open_roles_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CompanyListItem(BaseModel):
    uid: str
    company_name: str
    role: str
    location: str
    industry: Optional[str] = None
    logo_url: Optional[str] = None


class CompanySearchResult(BaseModel):
    items: list[CompanyListItem]
    total: int
    limit: int
    skip: int