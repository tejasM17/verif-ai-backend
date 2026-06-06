from typing import Optional

from app.repositories.base import BaseRepository
from app.models.student import Student


class StudentRepository(BaseRepository):
    collection_name = "students"

    async def get_by_firebase_uid(self, firebase_uid: str) -> Optional[Student]:
        data = await self.get_by_field("firebase_uid", firebase_uid)
        return Student(**data) if data else None

    async def get_by_email(self, email: str) -> Optional[Student]:
        data = await self.get_by_field("email", email)
        return Student(**data) if data else None

    async def create_student(self, **kwargs) -> Student:
        _, data = await self.create(**kwargs)
        return Student(**data)
