from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.profile import PublicProfile

class SearchQuery(BaseModel):
    skills: Optional[List[str]] = None
    min_trust: float = 0.0
    domain: Optional[str] = None
    location: Optional[str] = None
    limit: int = 20
    offset: int = 0

class SearchResult(BaseModel):
    profiles: List[PublicProfile]
    total: int
