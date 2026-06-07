from typing import Optional
from app.repositories.base import BaseRepository
from app.models.student_submission_summary import StudentSubmissionSummary


class StudentSubmissionSummaryRepository(BaseRepository):
    collection_name = "student_submission_summaries"

    async def get_by_student_id(self, student_id: str) -> Optional[StudentSubmissionSummary]:
        data = await self.get_by_field("student_id", student_id)
        return StudentSubmissionSummary(**data) if data else None

    async def get_by_firebase_uid(self, firebase_uid: str) -> Optional[StudentSubmissionSummary]:
        data = await self.get_by_field("student_firebase_uid", firebase_uid)
        return StudentSubmissionSummary(**data) if data else None

    async def create_summary(self, **kwargs) -> StudentSubmissionSummary:
        _, data = await self.create(**kwargs)
        return StudentSubmissionSummary(**data)
