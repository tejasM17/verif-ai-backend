import firebase_admin
from firebase_admin import credentials, auth, firestore
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings

bearer = HTTPBearer()

def init_firebase():
    if not firebase_admin._apps:
        creds_dict = settings.firebase_creds
        if not creds_dict:
            raise ValueError("FIREBASE_CREDENTIALS_JSON is invalid or empty")
        creds = credentials.Certificate(creds_dict)
        firebase_admin.initialize_app(creds)
    return firestore.client()

def get_firestore():
    return firestore.client()

async def verify_firebase_token(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    try:
        return auth.verify_id_token(creds.credentials)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

async def require_student(user = Depends(verify_firebase_token)) -> dict:
    if user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Students only")
    return user

async def require_recruiter(user = Depends(verify_firebase_token)) -> dict:
    if user.get("role") != "recruiter":
        raise HTTPException(status_code=403, detail="Recruiters only")
    return user
