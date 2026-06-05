from fastapi import APIRouter, Depends, HTTPException
from app.core.firebase import verify_firebase_token, require_student, get_firestore
from app.schemas.profile import StudentProfileUpdate, PublicProfile
from app.services.discovery_service import DiscoveryService

router = APIRouter()

@router.put("/update")
async def update_profile(
    update: StudentProfileUpdate,
    user: dict = Depends(require_student)
):
    """
    Update student profile details and optionally publish it.
    """
    profile = await DiscoveryService.publish_profile(user["uid"], update)
    return {"success": True, "data": profile}

@router.post("/publish")
async def publish_profile(user: dict = Depends(require_student)):
    """
    Make student profile public.
    """
    db = get_firestore()
    profile_ref = db.collection("profiles").document(user["uid"])
    doc = await profile_ref.get()
    
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Profile not found. Please update first.")
        
    await profile_ref.update({"is_public": True})
    return {"success": True, "message": "Profile published"}

@router.post("/unpublish")
async def unpublish_profile(user: dict = Depends(require_student)):
    """
    Make student profile private.
    """
    db = get_firestore()
    profile_ref = db.collection("profiles").document(user["uid"])
    await profile_ref.update({"is_public": False})
    return {"success": True, "message": "Profile unpublished"}

@router.get("/{uid}", response_model=PublicProfile)
async def get_profile(uid: str):
    """
    Get a public profile by UID. No auth required if public.
    """
    return await DiscoveryService.get_public_profile(uid)
