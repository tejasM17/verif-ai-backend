from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials
from app.schemas.auth import AuthRequest, UserResponse
from app.services.auth_service import AuthService
from app.core.security import security

router = APIRouter()
service = AuthService()


@router.get("/")
def home():
    return {"message": "VerifAI Backend Running"}


@router.post("/signup")
async def signup(req: AuthRequest):
    return service.signup(req.email, req.password)


@router.post("/login")
async def login(req: AuthRequest):
    return await service.login(req.email, req.password)


@router.get("/me", response_model=UserResponse)
def get_me(creds: HTTPAuthorizationCredentials = Depends(security)):
    return service.get_current_user(creds.credentials)
