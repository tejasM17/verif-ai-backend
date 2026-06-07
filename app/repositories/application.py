from typing import Optional
from app.repositories.base import BaseRepository
from app.models.application import Application


class ApplicationRepository(BaseRepository):
    collection_name = "applications"

    async def get_by_student_id(self, student_id: str, skip: int = 0, limit: int = 100) -> list[Application]:
        data_list = await self.get_all_by_field("student_id", student_id, skip, limit)
        return [Application(**d) for d in data_list]

    async def get_by_posting_and_student(self, posting_id: str, student_id: str) -> Optional[Application]:
        filters = [("posting_id", "==", posting_id), ("student_id", "==", student_id), ("is_active", "==", True)]
        data_list = await self.filter_by(filters, 0, 1)
        return Application(**data_list[0]) if data_list else None

    async def get_by_company_id(self, company_id: str, skip: int = 0, limit: int = 100) -> list[Application]:
        data_list = await self.get_all_by_field("company_id", company_id, skip, limit)
        return [Application(**d) for d in data_list]

    async def get_by_firebase_uid(self, firebase_uid: str, skip: int = 0, limit: int = 100) -> list[Application]:
        data_list = await self.get_all_by_field("student_firebase_uid", firebase_uid, skip, limit)
        return [Application(**d) for d in data_list]

    async def create_application(self, **kwargs) -> Application:
        _, data = await self.create(**kwargs)
        return Application(**data)

    async def count_by_student(self, student_id: str) -> int:
        data_list = await self.get_all_by_field("student_id", student_id, 0, 10000)
        return len(data_list)

    async def count_by_student_and_status(self, student_id: str, status: str) -> int:
        filters = [("student_id", "==", student_id), ("status", "==", status)]
        data_list = await self.filter_by(filters, 0, 10000)
        return len(data_list)
