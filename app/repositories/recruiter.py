from typing import Optional

from app.repositories.base import BaseRepository
from app.models.recruiter import Recruiter


class RecruiterRepository(BaseRepository):
    collection_name = "recruiters"

    async def get_by_firebase_uid(self, firebase_uid: str) -> Optional[Recruiter]:
        data = await self.get_by_field("firebase_uid", firebase_uid)
        return Recruiter(**data) if data else None

    async def get_by_email(self, email: str) -> Optional[Recruiter]:
        data = await self.get_by_field("email", email)
        return Recruiter(**data) if data else None

    async def create_recruiter(self, **kwargs) -> Recruiter:
        _, data = await self.create(**kwargs)
        return Recruiter(**data)
