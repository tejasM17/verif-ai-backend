from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class FileMetadata(BaseModel):
    file_id: str
    application_id: str
    student_id: str
    firebase_uid: str
    original_filename: str
    content_type: str
    file_size: int
    storage_key: str
    file_type: str
    uploaded_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
