from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class FileUploadResponse(BaseModel):
    file_id: str
    application_id: str
    original_filename: str
    content_type: str
    file_size: int
    file_type: str
    uploaded_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class FileDeleteResponse(BaseModel):
    message: str
