from fastapi import APIRouter, Depends, Query
from app.core.firebase import require_recruiter
from app.schemas.discover import SearchQuery, SearchResult
from app.schemas.profile import PublicProfile
from app.services.discovery_service import DiscoveryService
from typing import List, Optional

router = APIRouter()

@router.get("/", response_model=SearchResult)
async def list_profiles(
    limit: int = 20,
    offset: int = 0,
    user: dict = Depends(require_recruiter)
):
    """
    List all public profiles paginated.
    """
    query = SearchQuery(limit=limit, offset=offset)
    return await DiscoveryService.search_profiles(query)

@router.get("/search", response_model=SearchResult)
async def search_profiles(
    skills: Optional[List[str]] = Query(None),
    min_trust: float = 0.0,
    domain: Optional[str] = None,
    location: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    user: dict = Depends(require_recruiter)
):
    """
    Search public profiles with filters.
    """
    query = SearchQuery(
        skills=skills,
        min_trust=min_trust,
        domain=domain,
        location=location,
        limit=limit,
        offset=offset
    )
    return await DiscoveryService.search_profiles(query)

@router.post("/shortlist/{uid}")
async def shortlist_student(uid: str, user: dict = Depends(require_recruiter)):
    """
    Add student to recruiter's shortlist.
    """
    await DiscoveryService.shortlist_student(user["uid"], uid)
    return {"success": True, "message": "Student shortlisted"}

@router.get("/shortlist", response_model=List[PublicProfile])
async def get_shortlist(user: dict = Depends(require_recruiter)):
    """
    Get all shortlisted profiles for the recruiter.
    """
    return await DiscoveryService.get_shortlist(user["uid"])
