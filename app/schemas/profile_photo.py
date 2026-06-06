from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ProfilePhotoResponse(BaseModel):
    photo_url: str


class ProfilePhotoDocument(BaseModel):
    user_id: str
    firebase_uid: str
    filename: str
    content_type: str
    file_size: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
