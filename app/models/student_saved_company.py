from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class StudentSavedCompany(BaseModel):
    id: str
    student_id: str
    student_firebase_uid: str
    company_id: str
    created_at: Optional[datetime] = None
