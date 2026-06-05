from typing import List, Optional
from fastapi import HTTPException
from app.core.firebase import get_firestore
from app.schemas.profile import StudentProfileUpdate, PublicProfile
from app.schemas.discover import SearchQuery, SearchResult
from google.cloud.firestore_v1.base_query import FieldFilter
from datetime import datetime

class DiscoveryService:
    @staticmethod
    async def publish_profile(firebase_uid: str, update: StudentProfileUpdate) -> dict:
        db = get_firestore()
        profile_ref = db.collection("profiles").document(firebase_uid)
        
        # Get existing data to preserve trust_score and verdict
        doc = await profile_ref.get()
        existing_data = doc.to_dict() if doc.exists else {}
        
        profile_data = {
            "uid": firebase_uid,
            "skills": update.skills,
            "domain": update.domain,
            "location": update.location,
            "bio": update.bio,
            "is_public": update.is_public,
            "updated_at": datetime.utcnow()
        }
        
        # Merge with existing trust data
        profile_data["trust_score"] = existing_data.get("trust_score", 0.0)
        profile_data["verdict"] = existing_data.get("verdict", "N/A")
        profile_data["display_name"] = existing_data.get("display_name", "Anonymous")
        profile_data["verified_at"] = existing_data.get("verified_at")
        
        await profile_ref.set(profile_data, merge=True)
        return profile_data

    @staticmethod
    async def get_public_profile(firebase_uid: str) -> PublicProfile:
        db = get_firestore()
        doc = await db.collection("profiles").document(firebase_uid).get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Profile not found")
            
        data = doc.to_dict()
        if not data.get("is_public", False):
            raise HTTPException(status_code=403, detail="Profile is private")
            
        return PublicProfile(**data)

    @staticmethod
    async def search_profiles(query: SearchQuery) -> SearchResult:
        db = get_firestore()
        profiles_ref = db.collection("profiles")
        
        fs_query = profiles_ref.where(filter=FieldFilter("is_public", "==", True))
        
        if query.min_trust > 0:
            fs_query = fs_query.where(filter=FieldFilter("trust_score", ">=", query.min_trust))
            
        if query.domain:
            fs_query = fs_query.where(filter=FieldFilter("domain", "==", query.domain))
            
        if query.location:
            fs_query = fs_query.where(filter=FieldFilter("location", "==", query.location))

        if query.skills:
            fs_query = fs_query.where(filter=FieldFilter("skills", "array_contains_any", query.skills))

        # Order by trust_score
        fs_query = fs_query.order_by("trust_score", direction="DESCENDING")
        
        # Pagination
        fs_query = fs_query.offset(query.offset).limit(query.limit)
        
        docs = await fs_query.get()
        profiles = []
        for doc in docs:
            data = doc.to_dict()
            profiles.append(PublicProfile(**data))
            
        return SearchResult(profiles=profiles, total=len(profiles))

    @staticmethod
    async def shortlist_student(recruiter_uid: str, student_uid: str):
        db = get_firestore()
        shortlist_ref = db.collection("shortlists").document(recruiter_uid)
        
        doc = await shortlist_ref.get()
        if doc.exists:
            uids = doc.to_dict().get("student_uids", [])
            if student_uid not in uids:
                uids.append(student_uid)
                await shortlist_ref.update({"student_uids": uids})
        else:
            await shortlist_ref.set({"student_uids": [student_uid]})
            
    @staticmethod
    async def get_shortlist(recruiter_uid: str) -> List[PublicProfile]:
        db = get_firestore()
        shortlist_doc = await db.collection("shortlists").document(recruiter_uid).get()
        
        if not shortlist_doc.exists:
            return []
            
        student_uids = shortlist_doc.to_dict().get("student_uids", [])
        if not student_uids:
            return []
            
        profiles = []
        for uid in student_uids:
            doc = await db.collection("profiles").document(uid).get()
            if doc.exists:
                profiles.append(PublicProfile(**doc.to_dict()))
        
        return profiles
