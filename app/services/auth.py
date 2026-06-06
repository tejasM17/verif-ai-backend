import logging
from datetime import datetime, timezone, timedelta

from app.auth.firebase import verify_firebase_token
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
)
from app.repositories.student import StudentRepository
from app.repositories.recruiter import RecruiterRepository
from app.repositories.token_blacklist import TokenBlacklistRepository

logger = logging.getLogger("verifai")


class AuthService:
    def __init__(self):
        self.student_repo = StudentRepository()
        self.recruiter_repo = RecruiterRepository()
        self.token_blacklist_repo = TokenBlacklistRepository()

    async def register_student(self, firebase_token: str, full_name: str, phone=None,
                                profile_image=None, college_name=None, branch=None,
                                graduation_year=None, skills=None, resume_url=None) -> dict:
        decoded_token = await verify_firebase_token(firebase_token)
        firebase_uid = decoded_token["uid"]
        email = decoded_token.get("email", "")

        logger.info(
            "Register student: firebase_uid=%s email=%s checking collection=students",
            firebase_uid, email,
        )
        existing = await self.student_repo.get_by_firebase_uid(firebase_uid)
        if existing:
            raise ConflictException(
                "Student already registered",
                error_code="USER_ALREADY_REGISTERED",
            )

        logger.info(
            "Register student: firebase_uid=%s email=%s checking collection=recruiters",
            firebase_uid, email,
        )
        existing_rec = await self.recruiter_repo.get_by_firebase_uid(firebase_uid)
        if existing_rec:
            raise ConflictException(
                "This Firebase account is already registered as a recruiter",
                error_code="USER_ALREADY_REGISTERED",
            )

        student = await self.student_repo.create_student(
            firebase_uid=firebase_uid,
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
            user_id=student.id, firebase_uid=student.firebase_uid,
            email=student.email, role="student",
        )
        refresh_token = create_refresh_token(user_id=student.id, role="student")

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

    async def register_recruiter(self, firebase_token: str, company_name: str,
                                  recruiter_name: str, phone=None, company_website=None,
                                  company_logo=None, designation=None) -> dict:
        decoded_token = await verify_firebase_token(firebase_token)
        firebase_uid = decoded_token["uid"]
        email = decoded_token.get("email", "")

        logger.info(
            "Register recruiter: firebase_uid=%s email=%s checking collection=recruiters",
            firebase_uid, email,
        )
        existing = await self.recruiter_repo.get_by_firebase_uid(firebase_uid)
        if existing:
            raise ConflictException(
                "Recruiter already registered",
                error_code="USER_ALREADY_REGISTERED",
            )

        logger.info(
            "Register recruiter: firebase_uid=%s email=%s checking collection=students",
            firebase_uid, email,
        )
        existing_st = await self.student_repo.get_by_firebase_uid(firebase_uid)
        if existing_st:
            raise ConflictException(
                "This Firebase account is already registered as a student",
                error_code="USER_ALREADY_REGISTERED",
            )

        recruiter = await self.recruiter_repo.create_recruiter(
            firebase_uid=firebase_uid,
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
            user_id=recruiter.id, firebase_uid=recruiter.firebase_uid,
            email=recruiter.email, role="recruiter",
        )
        refresh_token = create_refresh_token(user_id=recruiter.id, role="recruiter")

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

    async def login(self, firebase_token: str) -> dict:
        decoded_token = await verify_firebase_token(firebase_token)
        firebase_uid = decoded_token["uid"]
        email = decoded_token.get("email", "")

        logger.info(
            "Login lookup: firebase_uid=%s email=%s collection=students field=firebase_uid",
            firebase_uid, email,
        )
        student = await self.student_repo.get_by_firebase_uid(firebase_uid)

        if student:
            if not student.is_active:
                logger.warning("Login blocked: student account disabled. firebase_uid=%s", firebase_uid)
                raise UnauthorizedException(
                    "Student account is disabled",
                    error_code="ACCOUNT_DISABLED",
                )
            access_token = create_access_token(
                user_id=student.id, firebase_uid=student.firebase_uid,
                email=student.email, role="student",
            )
            refresh_token = create_refresh_token(user_id=student.id, role="student")
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

        logger.info(
            "Login lookup: firebase_uid=%s email=%s collection=recruiters field=firebase_uid",
            firebase_uid, email,
        )
        recruiter = await self.recruiter_repo.get_by_firebase_uid(firebase_uid)

        if recruiter:
            if not recruiter.is_active:
                logger.warning("Login blocked: recruiter account disabled. firebase_uid=%s", firebase_uid)
                raise UnauthorizedException(
                    "Recruiter account is disabled",
                    error_code="ACCOUNT_DISABLED",
                )
            access_token = create_access_token(
                user_id=recruiter.id, firebase_uid=recruiter.firebase_uid,
                email=recruiter.email, role="recruiter",
            )
            refresh_token = create_refresh_token(user_id=recruiter.id, role="recruiter")
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

        logger.warning(
            "Login failed: user not registered. firebase_uid=%s email=%s",
            firebase_uid, email,
        )
        raise NotFoundException(
            "User not found. Please register first.",
            error_code="USER_NOT_REGISTERED",
        )

    async def get_user_by_token(self, access_token_str: str) -> dict:
        logger.info("/auth/me request received — verifying access token")
        payload = verify_access_token(access_token_str)

        firebase_uid = payload.get("firebase_uid")
        role = payload.get("role")
        user_id = payload.get("sub")

        logger.info("/auth/me token decoded — uid=%s role=%s sub=%s", firebase_uid, role, user_id)

        if role == "student":
            student = await self.student_repo.get_by_firebase_uid(firebase_uid)
            if not student:
                logger.warning("/auth/me student not found — firebase_uid=%s", firebase_uid)
                raise UnauthorizedException(
                    "Student not found",
                    error_code="USER_NOT_REGISTERED",
                )
            if not student.is_active:
                logger.warning("/auth/me student account disabled — firebase_uid=%s", firebase_uid)
                raise UnauthorizedException(
                    "Student account is disabled",
                    error_code="ACCOUNT_DISABLED",
                )
            logger.info("/auth/me student session restored — id=%s email=%s", student.id, student.email)
            return {
                "id": student.id,
                "email": student.email,
                "full_name": student.full_name,
                "role": "student",
                "is_active": student.is_active,
            }

        if role == "recruiter":
            recruiter = await self.recruiter_repo.get_by_firebase_uid(firebase_uid)
            if not recruiter:
                logger.warning("/auth/me recruiter not found — firebase_uid=%s", firebase_uid)
                raise UnauthorizedException(
                    "Recruiter not found",
                    error_code="USER_NOT_REGISTERED",
                )
            if not recruiter.is_active:
                logger.warning("/auth/me recruiter account disabled — firebase_uid=%s", firebase_uid)
                raise UnauthorizedException(
                    "Recruiter account is disabled",
                    error_code="ACCOUNT_DISABLED",
                )
            logger.info("/auth/me recruiter session restored — id=%s email=%s", recruiter.id, recruiter.email)
            return {
                "id": recruiter.id,
                "email": recruiter.email,
                "full_name": recruiter.recruiter_name,
                "role": "recruiter",
                "is_active": recruiter.is_active,
            }

        logger.warning("/auth/me unknown role in token — role=%s", role)
        raise UnauthorizedException(
            "Unknown user role",
            error_code="INVALID_TOKEN_TYPE",
        )

    async def refresh_token(self, refresh_token_str: str) -> dict:
        entry = await self.token_blacklist_repo.get_blacklist_entry(refresh_token_str)
        if entry is not None and entry.get("is_blacklisted", False):
            reason = entry.get("reason", "")
            logger.warning(
                "Refresh token reuse detected — token already blacklisted (reason=%s). "
                "Returning TOKEN_REUSED to frontend.",
                reason,
            )
            raise UnauthorizedException(
                "Refresh token has already been used. Please obtain a new one via login.",
                error_code="TOKEN_REUSED",
            )

        payload = verify_refresh_token(refresh_token_str)

        user_id = payload.get("sub")
        role = payload.get("role")

        logger.info(
            "Refresh token rotation — user_id=%s role=%s — blacklisting old token",
            user_id, role,
        )

        # Blacklist old refresh token (rotation) with reason="rotated"
        await self.token_blacklist_repo.blacklist_token(
            token=refresh_token_str, token_type="refresh",
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            reason="rotated",
        )

        if role == "student":
            student = await self.student_repo.get_by_field("id", user_id)
            if not student or not student.get("is_active"):
                raise UnauthorizedException(
                    "Student not found or inactive",
                    error_code="ACCOUNT_DISABLED",
                )
            new_access = create_access_token(
                user_id=user_id, firebase_uid=student["firebase_uid"],
                email=student["email"], role="student",
            )
            new_refresh = create_refresh_token(user_id=user_id, role="student")
        elif role == "recruiter":
            recruiter = await self.recruiter_repo.get_by_field("id", user_id)
            if not recruiter or not recruiter.get("is_active"):
                raise UnauthorizedException(
                    "Recruiter not found or inactive",
                    error_code="ACCOUNT_DISABLED",
                )
            new_access = create_access_token(
                user_id=user_id, firebase_uid=recruiter["firebase_uid"],
                email=recruiter["email"], role="recruiter",
            )
            new_refresh = create_refresh_token(user_id=user_id, role="recruiter")
        else:
            raise UnauthorizedException(
                "Invalid role in token",
                error_code="INVALID_TOKEN_TYPE",
            )

        logger.info("Token rotation complete — user_id=%s role=%s", user_id, role)

        return {"access_token": new_access, "refresh_token": new_refresh, "token_type": "bearer"}

    async def logout(self, access_token: str, refresh_token_str: str) -> None:
        logger.info(
            "Explicit logout called — blacklisting access and refresh tokens",
        )
        await self.token_blacklist_repo.blacklist_token(
            token=access_token, token_type="access",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            reason="logout",
        )
        await self.token_blacklist_repo.blacklist_token(
            token=refresh_token_str, token_type="refresh",
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            reason="logout",
        )
        logger.info("Logout complete — tokens blacklisted with reason=logout")
