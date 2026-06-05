from fastapi import APIRouter, Depends, HTTPException
from app.core.firebase import verify_firebase_token, require_student, require_recruiter, get_firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from typing import List

router = APIRouter()

@router.get("/my")
async def get_my_verification(user: dict = Depends(require_student)):
    """
    Get student's own latest verification results.
    """
    db = get_firestore()
    verifications = db.collection("verifications")\
        .where(filter=FieldFilter("student_uid", "==", user["uid"]))\
        .order_by("created_at", direction="DESCENDING")\
        .limit(1)
    
    docs = await verifications.get()
    if not docs:
        raise HTTPException(status_code=404, detail="No verifications found")
        
    data = docs[0].to_dict()
    data["id"] = docs[0].id
    return {"success": True, "data": data}

@router.get("/student/{uid}")
async def get_student_verification(uid: str, user: dict = Depends(require_recruiter)):
    """
    Get student's verification results for recruiter if profile is public.
    """
    db = get_firestore()
    
    # Check if public
    profile = await db.collection("profiles").document(uid).get()
    if not profile.exists or not profile.to_dict().get("is_public", False):
        raise HTTPException(status_code=403, detail="Profile is private or not found")
        
    verifications = db.collection("verifications")\
        .where(filter=FieldFilter("student_uid", "==", uid))\
        .order_by("created_at", direction="DESCENDING")\
        .limit(1)
        
    docs = await verifications.get()
    if not docs:
        raise HTTPException(status_code=404, detail="No verifications found")
        
    data = docs[0].to_dict()
    data["id"] = docs[0].id
    return {"success": True, "data": data}

@router.get("/logs/{result_id}")
async def get_research_logs(result_id: str, user: dict = Depends(verify_firebase_token)):
    """
    Get full research logs for a specific result.
    """
    db = get_firestore()
    logs_doc = await db.collection("research_logs").document(result_id).get()
    
    if not logs_doc.exists:
        raise HTTPException(status_code=404, detail="Logs not found")
        
    data = logs_doc.to_dict()
    
    # Permission check: owner or recruiter
    if user["uid"] != data["student_uid"] and user.get("role") != "recruiter":
        raise HTTPException(status_code=403, detail="Access denied")
        
    return {"success": True, "data": data}
