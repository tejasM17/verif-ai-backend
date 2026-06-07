from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.security import verify_access_token
from app.core.exceptions import UnauthorizedException, ForbiddenException
from app.models.student import Student
from app.models.recruiter import Recruiter
from app.repositories.student import StudentRepository
from app.repositories.recruiter import RecruiterRepository
from typing import Dict, Any

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    request: Request = None,
) -> Dict[str, Any]:
    token = None
    if credentials:
        token = credentials.credentials
    if not token and request:
        token = request.cookies.get("access_token")
    if not token:
        raise UnauthorizedException(
            "Not authenticated",
            error_code="NO_CREDENTIALS",
        )
    payload = verify_access_token(token)
    return payload


async def get_current_student(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Student:
    if current_user.get("role") != "student":
        raise ForbiddenException(
            "Access denied. Student role required.",
            error_code="ROLE_MISMATCH",
        )
    repo = StudentRepository()
    firebase_uid = current_user.get("firebase_uid")
    user_id = current_user.get("sub")
    student = await repo.get_by_firebase_uid(firebase_uid)
    if not student:
        student_data = await repo.get(user_id)
        if student_data:
            student = Student(**student_data)
    if not student or not student.is_active:
        raise UnauthorizedException(
            "Student not found or inactive",
            error_code="USER_NOT_FOUND",
        )
    return student


async def get_current_recruiter(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Recruiter:
    if current_user.get("role") != "recruiter":
        raise ForbiddenException(
            "Access denied. Recruiter role required.",
            error_code="ROLE_MISMATCH",
        )
    repo = RecruiterRepository()
    firebase_uid = current_user.get("firebase_uid")
    user_id = current_user.get("sub")
    recruiter = await repo.get_by_firebase_uid(firebase_uid)
    if not recruiter:
        recruiter_data = await repo.get(user_id)
        if recruiter_data:
            recruiter = Recruiter(**recruiter_data)
    if not recruiter or not recruiter.is_active:
        raise UnauthorizedException(
            "Recruiter not found or inactive",
            error_code="USER_NOT_FOUND",
        )
    return recruiter


async def get_current_admin(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    if current_user.get("role") != "admin":
        raise ForbiddenException(
            "Access denied. Admin role required.",
            error_code="ROLE_MISMATCH",
        )
    return current_user


def role_required(required_role: str):
    async def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        if current_user.get("role") != required_role:
            raise ForbiddenException(
                f"Access denied. {required_role.capitalize()} role required.",
                error_code="ROLE_MISMATCH",
            )
        return current_user
    return role_checker
