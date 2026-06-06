import uuid
from datetime import datetime, timezone, timedelta

from jose import JWTError

from app.auth.firebase import verify_firebase_token
from app.core.security import (
    create_access_token,
    create_refresh_token,
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

        existing = await self.student_repo.get_by_firebase_uid(firebase_uid)
        if existing:
            raise ConflictException("Student already registered")

        existing_rec = await self.recruiter_repo.get_by_firebase_uid(firebase_uid)
        if existing_rec:
            raise ConflictException("This Firebase account is already registered as a recruiter")

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

        existing = await self.recruiter_repo.get_by_firebase_uid(firebase_uid)
        if existing:
            raise ConflictException("Recruiter already registered")

        existing_st = await self.student_repo.get_by_firebase_uid(firebase_uid)
        if existing_st:
            raise ConflictException("This Firebase account is already registered as a student")

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

        student = await self.student_repo.get_by_firebase_uid(firebase_uid)
        if student:
            if not student.is_active:
                raise UnauthorizedException("Student account is deactivated")
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

        recruiter = await self.recruiter_repo.get_by_firebase_uid(firebase_uid)
        if recruiter:
            if not recruiter.is_active:
                raise UnauthorizedException("Recruiter account is deactivated")
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

        raise NotFoundException("User not found. Please register first.")

    async def refresh_token(self, refresh_token_str: str) -> dict:
        if await self.token_blacklist_repo.is_blacklisted(refresh_token_str):
            raise UnauthorizedException("Refresh token has been revoked")

        try:
            payload = verify_refresh_token(refresh_token_str)
        except JWTError:
            raise UnauthorizedException("Invalid or expired refresh token")

        user_id = payload.get("sub")
        role = payload.get("role")

        if role == "student":
            student_data = await self.student_repo.get(user_id)
            if not student_data:
                raise UnauthorizedException("Student not found")
            student = await self.student_repo.get_by_field("id", user_id)
            if not student or not student.get("is_active"):
                raise UnauthorizedException("Student not found or inactive")
            new_access = create_access_token(
                user_id=user_id, firebase_uid=student["firebase_uid"],
                email=student["email"], role="student",
            )
            new_refresh = create_refresh_token(user_id=user_id, role="student")
        elif role == "recruiter":
            recruiter = await self.recruiter_repo.get_by_field("id", user_id)
            if not recruiter or not recruiter.get("is_active"):
                raise UnauthorizedException("Recruiter not found or inactive")
            new_access = create_access_token(
                user_id=user_id, firebase_uid=recruiter["firebase_uid"],
                email=recruiter["email"], role="recruiter",
            )
            new_refresh = create_refresh_token(user_id=user_id, role="recruiter")
        else:
            raise UnauthorizedException("Invalid role in token")

        return {"access_token": new_access, "refresh_token": new_refresh, "token_type": "bearer"}

    async def logout(self, access_token: str, refresh_token_str: str) -> None:
        await self.token_blacklist_repo.blacklist_token(
            token=access_token, token_type="access",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
        )
        await self.token_blacklist_repo.blacklist_token(
            token=refresh_token_str, token_type="refresh",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
