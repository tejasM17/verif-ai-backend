from typing import Optional
from app.repositories.base import BaseRepository
from app.models.student_saved_company import StudentSavedCompany


class StudentSavedCompanyRepository(BaseRepository):
    collection_name = "student_saved_companies"

    async def get_by_student(self, student_id: str, skip: int = 0, limit: int = 100) -> list[StudentSavedCompany]:
        data_list = await self.get_all_by_field("student_id", student_id, skip, limit)
        return [StudentSavedCompany(**d) for d in data_list]

    async def get_by_student_and_company(self, student_id: str, company_id: str) -> Optional[StudentSavedCompany]:
        filters = [("student_id", "==", student_id), ("company_id", "==", company_id)]
        data_list = await self.filter_by(filters, 0, 1)
        return StudentSavedCompany(**data_list[0]) if data_list else None

    async def create_saved(self, **kwargs) -> StudentSavedCompany:
        _, data = await self.create(**kwargs)
        return StudentSavedCompany(**data)

    async def delete_by_student_and_company(self, student_id: str, company_id: str) -> bool:
        saved = await self.get_by_student_and_company(student_id, company_id)
        if not saved:
            return False
        return await self.delete(saved.id)

    async def count_by_student(self, student_id: str) -> int:
        data_list = await self.get_all_by_field("student_id", student_id, 0, 10000)
        return len(data_list)
