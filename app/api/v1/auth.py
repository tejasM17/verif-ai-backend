from fastapi import APIRouter, Depends
from app.schemas.auth import (
    AuthRequest,
    GoogleAuthRequest,
    GithubAuthRequest,
    UserResponse,
)
from app.services.auth_service import AuthService
from app.api.dependencies import get_current_user

router = APIRouter()
service = AuthService()


@router.get("/")
def home():
    return {"message": "VerifAI Backend Running"}


@router.post("/signup")
async def signup(req: AuthRequest):
    return service.signup(req.email, req.password, req.role)


@router.post("/login")
async def login(req: AuthRequest):
    return await service.login(req.email, req.password)


@router.post("/google")
def google_login(req: GoogleAuthRequest):
    return service.google_login(req.id_token)


@router.post("/github")
def github_login(req: GithubAuthRequest):
    return service.github_login(req.id_token)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: dict = Depends(get_current_user)):
    return current_user
