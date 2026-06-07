import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from app.auth.firebase import verify_firebase_token
from app.auth.password import hash_password, verify_password
from app.config.settings import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_access_token,
    verify_refresh_token,
)
from app.core.exceptions import (
    ConflictException,
    UnauthorizedException,
    NotFoundException,
    ValidationException,
    AppException,
)
from app.repositories.auth_repository import AuthRepository, MongoAuthRepository
from app.repositories.student import StudentRepository
from app.repositories.recruiter import RecruiterRepository

logger = logging.getLogger("verifai")


class AuthService:
    def __init__(self, auth_repo: Optional[AuthRepository] = None):
        self.auth_repo = auth_repo or MongoAuthRepository()
        self.student_repo = StudentRepository()
        self.recruiter_repo = RecruiterRepository()

    def _log(self, request_id: str, msg: str, *args) -> None:
        prefix = f"[{request_id}]" if request_id else ""
        logger.info(f"{prefix} {msg}", *args)

    def _log_warn(self, request_id: str, msg: str, *args) -> None:
        prefix = f"[{request_id}]" if request_id else ""
        logger.warning(f"{prefix} {msg}", *args)

    async def register_student(self, full_name: str, email: Optional[str] = None,
                                password: Optional[str] = None, firebase_token: Optional[str] = None,
                                phone=None, profile_image=None, college_name=None,
                                branch=None, graduation_year=None, skills=None,
                                resume_url=None, request_id: str = "") -> dict:
        if not email and not firebase_token:
            raise ValidationException(
                "Either email or firebase_token is required",
                error_code="VALIDATION_ERROR",
            )
        if email and not password and not firebase_token:
            raise ValidationException(
                "Password is required when using email registration",
                error_code="VALIDATION_ERROR",
            )

        firebase_uid = None
        if firebase_token:
            decoded = await verify_firebase_token(firebase_token)
            firebase_uid = decoded["uid"]
            email = email or decoded.get("email", "")

        existing_user = await self.auth_repo.get_user_by_email(email)
        if existing_user:
            raise ConflictException(
                "A user with this email already exists",
                error_code="USER_ALREADY_REGISTERED",
            )
        if firebase_uid:
            existing_fb = await self.auth_repo.get_user_by_firebase_uid(firebase_uid)
            if existing_fb:
                raise ConflictException(
                    "This Firebase account is already registered",
                    error_code="USER_ALREADY_REGISTERED",
                )

        existing_profile = await self.student_repo.get_by_email(email)
        if existing_profile:
            raise ConflictException(
                "Student already registered",
                error_code="USER_ALREADY_REGISTERED",
            )

        password_hash = hash_password(password) if password else None
        user = await self.auth_repo.create_user(
            email=email,
            password_hash=password_hash,
            firebase_uid=firebase_uid,
            role="student",
        )

        profile_firebase_uid = firebase_uid or user.id
        student = await self.student_repo.create_student(
            id=user.id,
            firebase_uid=profile_firebase_uid,
            full_name=full_name,
            email=email,
            phone=phone,
            profile_image=profile_image,
            college_name=college_name,
            branch=branch,
            graduation_year=graduation_year,
            skills=skills,
            resume_url=resume_url,
            role="student",
        )

        access_token = create_access_token(
            user_id=user.id, firebase_uid=profile_firebase_uid,
            email=email, role="student",
        )
        refresh_token = create_refresh_token(user_id=user.id, role="student")

        self._log(request_id, "register_student: user_id=%s role=student", user.id)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": student.id,
                "email": student.email,
                "full_name": student.full_name,
                "role": "student",
            },
        }

    async def register_recruiter(self, company_name: str, recruiter_name: str,
                                  email: Optional[str] = None, password: Optional[str] = None,
                                  firebase_token: Optional[str] = None, phone=None,
                                  company_website=None, company_logo=None,
                                  designation=None, request_id: str = "") -> dict:
        if not email and not firebase_token:
            raise ValidationException(
                "Either email or firebase_token is required",
                error_code="VALIDATION_ERROR",
            )
        if email and not password and not firebase_token:
            raise ValidationException(
                "Password is required when using email registration",
                error_code="VALIDATION_ERROR",
            )

        firebase_uid = None
        if firebase_token:
            decoded = await verify_firebase_token(firebase_token)
            firebase_uid = decoded["uid"]
            email = email or decoded.get("email", "")

        existing_user = await self.auth_repo.get_user_by_email(email)
        if existing_user:
            raise ConflictException(
                "A user with this email already exists",
                error_code="USER_ALREADY_REGISTERED",
            )
        if firebase_uid:
            existing_fb = await self.auth_repo.get_user_by_firebase_uid(firebase_uid)
            if existing_fb:
                raise ConflictException(
                    "This Firebase account is already registered",
                    error_code="USER_ALREADY_REGISTERED",
                )

        existing_profile = await self.recruiter_repo.get_by_email(email)
        if existing_profile:
            raise ConflictException(
                "Recruiter already registered",
                error_code="USER_ALREADY_REGISTERED",
            )

        password_hash = hash_password(password) if password else None
        user = await self.auth_repo.create_user(
            email=email,
            password_hash=password_hash,
            firebase_uid=firebase_uid,
            role="recruiter",
        )

        recruiter = await self.recruiter_repo.create_recruiter(
            id=user.id,
            firebase_uid=firebase_uid or user.id,
            company_name=company_name,
            recruiter_name=recruiter_name,
            email=email,
            phone=phone,
            company_website=company_website,
            company_logo=company_logo,
            designation=designation,
            role="recruiter",
        )

        access_token = create_access_token(
            user_id=user.id, firebase_uid=firebase_uid or user.id,
            email=email, role="recruiter",
        )
        refresh_token = create_refresh_token(user_id=user.id, role="recruiter")

        self._log(request_id, "register_recruiter: user_id=%s role=recruiter", user.id)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": recruiter.id,
                "email": recruiter.email,
                "full_name": recruiter.recruiter_name,
                "role": "recruiter",
            },
        }

    async def login(self, email: Optional[str] = None, password: Optional[str] = None,
                     firebase_token: Optional[str] = None, request_id: str = "") -> dict:
        if not firebase_token and not email:
            raise ValidationException(
                "Either email or firebase_token is required",
                error_code="VALIDATION_ERROR",
            )

        user = None
        if firebase_token:
            decoded = await verify_firebase_token(firebase_token)
            firebase_uid = decoded["uid"]
            email = decoded.get("email", "")
            user = await self.auth_repo.get_user_by_firebase_uid(firebase_uid)
            if not user:
                user = await self.auth_repo.get_user_by_email(email)

        elif email and password:
            user = await self.auth_repo.get_user_by_email(email)
            if not user:
                raise NotFoundException(
                    "User not found. Please register first.",
                    error_code="USER_NOT_REGISTERED",
                )
            if not user.password_hash:
                raise UnauthorizedException(
                    "This account uses Firebase login. Please sign in with Firebase.",
                    error_code="INVALID_LOGIN_METHOD",
                )
            if not verify_password(password, user.password_hash):
                raise UnauthorizedException(
                    "Invalid email or password",
                    error_code="INVALID_CREDENTIALS",
                )

        if not user:
            raise NotFoundException(
                "User not found. Please register first.",
                error_code="USER_NOT_REGISTERED",
            )

        if not user.is_active:
            raise UnauthorizedException(
                "Account is disabled",
                error_code="ACCOUNT_DISABLED",
            )

        role = user.role

        profile = None
        if role == "student":
            profile = await self.student_repo.get_by_firebase_uid(user.firebase_uid or user.id)
            if not profile:
                profile = await self.student_repo.get_by_email(user.email)
        elif role == "recruiter":
            profile = await self.recruiter_repo.get_by_firebase_uid(user.firebase_uid or user.id)
            if not profile:
                profile = await self.recruiter_repo.get_by_email(user.email)

        access_token = create_access_token(
            user_id=user.id, firebase_uid=user.firebase_uid or user.id,
            email=user.email, role=role,
        )
        refresh_token = create_refresh_token(user_id=user.id, role=role)

        self._log(request_id, "login: user_id=%s role=%s", user.id, role)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": profile.full_name if profile and hasattr(profile, 'full_name')
                             else getattr(profile, 'recruiter_name', user.email),
                "role": role,
            },
        }

    async def get_user_by_token(self, access_token_str: str, request_id: str = "") -> dict:
        payload = verify_access_token(access_token_str)
        firebase_uid = payload.get("firebase_uid")
        role = payload.get("role")
        user_id = payload.get("sub")

        self._log(request_id, "get_user_by_token: user_id=%s role=%s", user_id, role)

        user = await self.auth_repo.get_user_by_id(user_id)
        if not user:
            raise UnauthorizedException(
                "User not found", error_code="USER_NOT_REGISTERED",
            )
        if not user.is_active:
            raise UnauthorizedException(
                "Account is disabled", error_code="ACCOUNT_DISABLED",
            )

        if role == "student":
            profile = await self.student_repo.get_by_firebase_uid(firebase_uid)
            if not profile:
                profile = await self.student_repo.get(user_id)
            if not profile:
                raise UnauthorizedException(
                    "Student not found", error_code="USER_NOT_REGISTERED",
                )
            return {
                "id": profile.id,
                "email": profile.email,
                "full_name": profile.full_name,
                "role": "student",
                "is_active": profile.is_active,
            }

        if role == "recruiter":
            profile = await self.recruiter_repo.get_by_firebase_uid(firebase_uid)
            if not profile:
                profile = await self.recruiter_repo.get(user_id)
            if not profile:
                raise UnauthorizedException(
                    "Recruiter not found", error_code="USER_NOT_REGISTERED",
                )
            return {
                "id": profile.id,
                "email": profile.email,
                "full_name": profile.recruiter_name,
                "role": "recruiter",
                "is_active": profile.is_active,
            }

        raise UnauthorizedException(
            "Unknown user role", error_code="INVALID_TOKEN_TYPE",
        )

    async def refresh_token(self, refresh_token_str: str, request_id: str = "") -> dict:
        blacklisted = await self.auth_repo.is_token_blacklisted(refresh_token_str)
        if blacklisted:
            self._log_warn(request_id, "refresh_token: reuse detected — returning TOKEN_REUSED")
            raise UnauthorizedException(
                "Refresh token has already been used",
                error_code="TOKEN_REUSED",
            )

        payload = verify_refresh_token(refresh_token_str)
        user_id = payload.get("sub")
        role = payload.get("role")

        await self.auth_repo.blacklist_token(
            token=refresh_token_str, token_type="refresh",
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            reason="rotated",
        )

        user = await self.auth_repo.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise UnauthorizedException(
                "User not found or inactive", error_code="ACCOUNT_DISABLED",
            )

        new_access = create_access_token(
            user_id=user_id, firebase_uid=user.firebase_uid or user_id,
            email=user.email, role=role,
        )
        new_refresh = create_refresh_token(user_id=user_id, role=role)

        self._log(request_id, "refresh_token: user_id=%s role=%s — rotated", user_id, role)

        return {"access_token": new_access, "refresh_token": new_refresh, "token_type": "bearer"}

    async def logout(self, access_token: str, refresh_token_str: str, request_id: str = "") -> None:
        self._log(request_id, "logout: blacklisting access and refresh tokens")
        await self.auth_repo.blacklist_token(
            token=access_token, token_type="access",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            reason="logout",
        )
        if refresh_token_str:
            await self.auth_repo.blacklist_token(
                token=refresh_token_str, token_type="refresh",
                expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
                reason="logout",
            )
