from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class StudentSubmissionSummary(BaseModel):
    id: str
    student_id: str
    student_firebase_uid: str
    total_applications: int = 0
    submitted_count: int = 0
    reviewing_count: int = 0
    selected_count: int = 0
    rejected_count: int = 0
    saved_companies_count: int = 0
    updated_at: Optional[datetime] = None
