import asyncio

from fastapi import HTTPException, status

from app.repositories.company_repository import CompanyRepository
from app.repositories.job_repository import JobRepository


_job_repo = JobRepository()
_company_repo = CompanyRepository()


def _enrich(job: dict | None, company: dict | None) -> dict | None:
    if job is None:
        return None
    company = company or {}
    enriched = dict(job)
    enriched["company_name"] = company.get("company_name")
    enriched["company_logo_url"] = company.get("logo_url")
    return enriched


async def _resolve_company_for_recruiter(recruiter_uid: str, company_uid: str) -> dict:
    """Look up the company, auto-provisioning a stub on first use.

    Ownership invariant: the route handler derives `company_uid` from the
    authenticated recruiter's own `uid` (see app/api/v1/jobs.py), so the two
    values are guaranteed equal by the time we get here. We still do an
    integrity check in case a future caller passes a mismatched pair.
    """
    if company_uid != recruiter_uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to manage jobs for another recruiter",
        )

    company = await asyncio.to_thread(_company_repo.get_by_uid, company_uid)
    if company:
        return company

    await asyncio.to_thread(_company_repo.upsert_minimal, company_uid, recruiter_uid)
    fetched = await asyncio.to_thread(_company_repo.get_by_uid, company_uid)
    if not fetched:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to provision company record",
        )
    return fetched


class JobService:
    def __init__(self) -> None:
        self.repo = _job_repo
        self.company_repo = _company_repo

    async def create_for_my_company(
        self, recruiter_uid: str, company_uid: str, data: dict
    ) -> dict:
        company = await _resolve_company_for_recruiter(recruiter_uid, company_uid)
        job = await self.repo.create(recruiter_uid, company_uid, data)
        return _enrich(job, company)

    async def list_for_company(
        self, company_uid: str, status_filter: str | None, limit: int, skip: int
    ) -> tuple[list[dict], int]:
        company = await asyncio.to_thread(self.company_repo.get_by_uid, company_uid)
        items, total = await self.repo.list_by_company(
            company_uid=company_uid, status=status_filter, limit=limit, skip=skip
        )
        return [_enrich(item, company) for item in items], total

    async def list_for_recruiter(
        self, recruiter_uid: str, status_filter: str | None, limit: int, skip: int
    ) -> tuple[list[dict], int]:
        items, total = await self.repo.list_by_recruiter(
            recruiter_uid=recruiter_uid, status=status_filter, limit=limit, skip=skip
        )

        company_cache: dict[str, dict | None] = {}

        async def _cached_company(uid: str) -> dict | None:
            if uid not in company_cache:
                company_cache[uid] = await asyncio.to_thread(
                    self.company_repo.get_by_uid, uid
                )
            return company_cache[uid]

        enriched: list[dict] = []
        for item in items:
            company = await _cached_company(item["company_uid"])
            enriched.append(_enrich(item, company))
        return enriched, total

    async def get_job(self, uid: str) -> dict:
        job = await self.repo.get_by_uid(uid)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
            )
        company = await asyncio.to_thread(
            self.company_repo.get_by_uid, job["company_uid"]
        )
        return _enrich(job, company)

    async def update_job(self, recruiter_uid: str, uid: str, data: dict) -> dict:
        job = await self.repo.get_by_uid(uid)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
            )
        if job.get("recruiter_uid") != recruiter_uid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this job",
            )
        updated = await self.repo.update(uid, data)
        company = (
            await asyncio.to_thread(self.company_repo.get_by_uid, updated["company_uid"])
            if updated
            else None
        )
        return _enrich(updated, company)

    async def delete_job(self, recruiter_uid: str, uid: str) -> bool:
        job = await self.repo.get_by_uid(uid)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
            )
        if job.get("recruiter_uid") != recruiter_uid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this job",
            )
        return await self.repo.delete(uid)


__all__ = ["JobService"]