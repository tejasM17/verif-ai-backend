from typing import Optional

from app.core.exceptions import NotFoundException
from app.models.student import Student
from app.repositories.student import StudentRepository


class StudentService:
    def __init__(self):
        self.repo = StudentRepository()

    async def update_profile(self, student: Student, **kwargs) -> Student:
        data = {k: v for k, v in kwargs.items() if v is not None}
        if not data:
            return student
        success = await self.repo.update(student.id, **data)
        if not success:
            raise NotFoundException("Student not found")
        updated = await self.repo.get(student.id)
        return Student(**updated) if updated else student

    async def delete_profile(self, student: Student) -> None:
        success = await self.repo.delete(student.id)
        if not success:
            raise NotFoundException("Student not found")
