import logging
from fastapi import APIRouter, Depends, Request, Response
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
from app.core.exceptions import UnauthorizedException, AppException
from app.config.settings import settings

logger = logging.getLogger("verifai")

router = APIRouter(prefix="/auth", tags=["Authentication"])
security_scheme = HTTPBearer(auto_error=False)


def _set_auth_cookies(response: Response, tokens: dict) -> None:
    response.set_cookie(
        key="access_token",
        value=tokens["access_token"],
        httponly=True,
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=tokens["refresh_token"],
        httponly=True,
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/",
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")


def _extract_access_token(
    credentials: HTTPAuthorizationCredentials,
    request: Request,
) -> str | None:
    if credentials:
        return credentials.credentials
    token = request.cookies.get("access_token")
    return token


@router.post("/register/student")
async def register_student(request: StudentRegisterRequest, response: Response, http_request: Request):
    service = AuthService()
    rid = getattr(http_request.state, "request_id", "")
    result = await service.register_student(
        firebase_token=request.firebase_token,
        email=request.email,
        password=request.password,
        full_name=request.full_name,
        phone=request.phone,
        profile_image=request.profile_image,
        college_name=request.college_name,
        branch=request.branch,
        graduation_year=request.graduation_year,
        skills=request.skills,
        resume_url=request.resume_url,
        request_id=rid,
    )
    _set_auth_cookies(response, result)
    return success_response(data=result, message="Student registered successfully")


@router.post("/register/recruiter")
async def register_recruiter(request: RecruiterRegisterRequest, response: Response, http_request: Request):
    service = AuthService()
    rid = getattr(http_request.state, "request_id", "")
    result = await service.register_recruiter(
        firebase_token=request.firebase_token,
        email=request.email,
        password=request.password,
        company_name=request.company_name,
        recruiter_name=request.recruiter_name,
        phone=request.phone,
        company_website=request.company_website,
        company_logo=request.company_logo,
        designation=request.designation,
        request_id=rid,
    )
    _set_auth_cookies(response, result)
    return success_response(data=result, message="Recruiter registered successfully")


@router.post("/login")
async def login(request: LoginRequest, response: Response, http_request: Request):
    service = AuthService()
    rid = getattr(http_request.state, "request_id", "")
    result = await service.login(
        email=request.email,
        password=request.password,
        firebase_token=request.firebase_token,
        request_id=rid,
    )
    _set_auth_cookies(response, result)
    return success_response(data=result, message="Login successful")


@router.post("/refresh")
async def refresh_token(request: RefreshTokenRequest, response: Response, http_request: Request):
    refresh_token_str = request.refresh_token or http_request.cookies.get("refresh_token")
    if not refresh_token_str:
        raise UnauthorizedException(
            "Refresh token is required",
            error_code="NO_CREDENTIALS",
        )
    service = AuthService()
    result = await service.refresh_token(
        refresh_token_str=refresh_token_str,
        request_id=getattr(http_request.state, "request_id", ""),
    )
    _set_auth_cookies(response, result)
    return success_response(data=result, message="Token refreshed successfully")


@router.get("/me")
async def get_current_user_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    request: Request = None,
    response: Response = None,
):
    access_token = _extract_access_token(credentials, request)
    if not access_token:
        raise UnauthorizedException(
            "Not authenticated",
            error_code="NO_CREDENTIALS",
        )
    service = AuthService()
    rid = getattr(request.state, "request_id", "") if request else ""
    try:
        user = await service.get_user_by_token(access_token_str=access_token, request_id=rid)
        return success_response(data=user, message="User session restored")
    except UnauthorizedException as e:
        if e.error_code != "TOKEN_EXPIRED":
            raise
    refresh_token_str = request.cookies.get("refresh_token") if request else None
    if not refresh_token_str:
        raise UnauthorizedException(
            "Session expired. Please log in again.",
            error_code="TOKEN_EXPIRED",
        )
    try:
        tokens = await service.refresh_token(refresh_token_str=refresh_token_str, request_id=rid)
        _set_auth_cookies(response, tokens)
        user = await service.get_user_by_token(access_token_str=tokens["access_token"], request_id=rid)
        return success_response(
            data={**user, "access_token": tokens["access_token"], "refresh_token": tokens["refresh_token"]},
            message="Session restored",
        )
    except (UnauthorizedException, AppException):
        _clear_auth_cookies(response)
        raise UnauthorizedException(
            "Session expired. Please log in again.",
            error_code="TOKEN_EXPIRED",
        )


@router.post("/logout")
async def logout(
    request: LogoutRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    http_request: Request = None,
    response: Response = None,
):
    access_token = _extract_access_token(credentials, http_request)
    if not access_token:
        _clear_auth_cookies(response)
        return success_response(message="Logged out successfully")
    refresh_token_str = request.refresh_token or http_request.cookies.get("refresh_token")
    service = AuthService()
    rid = getattr(http_request.state, "request_id", "") if http_request else ""
    await service.logout(
        access_token=access_token,
        refresh_token_str=refresh_token_str or "",
        request_id=rid,
    )
    _clear_auth_cookies(response)
    return success_response(message="Logged out successfully")
