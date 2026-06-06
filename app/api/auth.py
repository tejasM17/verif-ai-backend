from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schemas.auth import (
    StudentRegisterRequest,
    RecruiterRegisterRequest,
    LoginRequest,
    RefreshTokenRequest,
    LogoutRequest,
)
from app.services.auth import AuthService
from app.core.dependencies import get_current_user
from app.core.response import success_response
from app.core.exceptions import UnauthorizedException

router = APIRouter(prefix="/auth", tags=["Authentication"])
security_scheme = HTTPBearer(auto_error=False)


@router.post("/student/register")
async def register_student(request: StudentRegisterRequest):
    service = AuthService()
    result = await service.register_student(
        firebase_token=request.firebase_token,
        full_name=request.full_name,
        phone=request.phone,
        profile_image=request.profile_image,
        college_name=request.college_name,
        branch=request.branch,
        graduation_year=request.graduation_year,
        skills=request.skills,
        resume_url=request.resume_url,
    )
    return success_response(data=result, message="Student registered successfully")


@router.post("/recruiter/register")
async def register_recruiter(request: RecruiterRegisterRequest):
    service = AuthService()
    result = await service.register_recruiter(
        firebase_token=request.firebase_token,
        company_name=request.company_name,
        recruiter_name=request.recruiter_name,
        phone=request.phone,
        company_website=request.company_website,
        company_logo=request.company_logo,
        designation=request.designation,
    )
    return success_response(data=result, message="Recruiter registered successfully")


@router.post("/login")
async def login(request: LoginRequest):
    service = AuthService()
    result = await service.login(firebase_token=request.firebase_token)
    return success_response(data=result, message="Login successful")


@router.post("/refresh")
async def refresh_token(request: RefreshTokenRequest):
    service = AuthService()
    result = await service.refresh_token(refresh_token_str=request.refresh_token)
    return success_response(data=result, message="Token refreshed successfully")


@router.get("/me")
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
):
    if not credentials:
        raise UnauthorizedException(
            "Not authenticated",
            error_code="NO_CREDENTIALS",
        )
    service = AuthService()
    user = await service.get_user_by_token(access_token_str=credentials.credentials)
    return success_response(data=user, message="User session restored")


@router.post("/logout")
async def logout(
    request: LogoutRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
):
    if not credentials:
        raise UnauthorizedException(
            "Not authenticated",
            error_code="NO_CREDENTIALS",
        )
    service = AuthService()
    await service.logout(
        access_token=credentials.credentials,
        refresh_token_str=request.refresh_token,
    )
    return success_response(message="Logged out successfully")
