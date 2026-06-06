from typing import Optional

from app.core.exceptions import NotFoundException
from app.models.recruiter import Recruiter
from app.repositories.recruiter import RecruiterRepository


class RecruiterService:
    def __init__(self):
        self.repo = RecruiterRepository()

    async def update_profile(self, recruiter: Recruiter, **kwargs) -> Recruiter:
        data = {k: v for k, v in kwargs.items() if v is not None}
        if not data:
            return recruiter
        success = await self.repo.update(recruiter.id, **data)
        if not success:
            raise NotFoundException("Recruiter not found")
        updated = await self.repo.get(recruiter.id)
        return Recruiter(**updated) if updated else recruiter

    async def delete_profile(self, recruiter: Recruiter) -> None:
        success = await self.repo.delete(recruiter.id)
        if not success:
            raise NotFoundException("Recruiter not found")
