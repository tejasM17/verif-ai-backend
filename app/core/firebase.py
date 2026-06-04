import json
import firebase_admin
from firebase_admin import credentials, auth, firestore
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings

bearer = HTTPBearer()
firestore_db = None

def init_firebase():
    global firestore_db
    try:
        # Check if already initialized
        firebase_admin.get_app()
    except ValueError:
        creds_dict = settings.firebase_creds_dict
        creds = credentials.Certificate(creds_dict)
        firebase_admin.initialize_app(creds)
    
    firestore_db = firestore.client()
    print("✅ Firebase initialized")

def get_firestore():
    return firestore_db

async def verify_firebase_token(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    try:
        return auth.verify_id_token(creds.credentials)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

async def require_student(user: dict = Depends(verify_firebase_token)) -> dict:
    if user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Access forbidden: Students only")
    return user

async def require_recruiter(user: dict = Depends(verify_firebase_token)) -> dict:
    if user.get("role") != "recruiter":
        raise HTTPException(status_code=403, detail="Access forbidden: Recruiters only")
    return user
