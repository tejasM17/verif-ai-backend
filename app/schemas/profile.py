from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class StudentProfileUpdate(BaseModel):
    skills: List[str]
    domain: str
    location: str
    bio: str
    is_public: bool

class PublicProfile(BaseModel):
    uid: str
    display_name: str
    trust_score: float
    verdict: str
    skills: List[str]
    domain: str
    location: str
    bio: str
    verified_at: Optional[datetime] = None
