from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class User(BaseModel):
    id: str
    email: str
    password_hash: Optional[str] = None
    firebase_uid: Optional[str] = None
    role: str = "student"
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
