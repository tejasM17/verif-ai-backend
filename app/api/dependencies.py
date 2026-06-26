from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from app.core.security import security, verify_token
from app.services.user_service import UserService

user_service = UserService()


def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    decoded = verify_token(creds.credentials)
    if not decoded:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )
    profile = user_service.get_or_create_profile(
        uid=decoded["uid"],
        email=decoded.get("email", ""),
        display_name=decoded.get("name"),
        photo_url=decoded.get("picture"),
    )
    return {
        "uid": decoded["uid"],
        "email": decoded.get("email", ""),
        "displayName": decoded.get("name"),
        "photoUrl": decoded.get("picture"),
        "role": profile.get("role"),
    }


def require_role(required_role: str):
    def checker(current_user: dict = Depends(get_current_user)) -> dict:
        actual = current_user.get("role")
        if actual == required_role:
            return current_user
        # Surface a helpful message that explains *why* the gate fired and what
        # the user can do about it, instead of a generic 403.
        actual_label = actual if actual else "none"
        if required_role == "recruiter" and actual in (None, "student"):
            detail = (
                f"This account is registered as '{actual_label}'. "
                "To manage roles for a company, sign out and create a recruiter account, "
                "or update your role at POST /profile/role."
            )
        elif required_role == "student" and actual in (None, "recruiter"):
            detail = (
                f"This account is registered as '{actual_label}'. "
                "To apply for jobs, sign out and create a student account, "
                "or update your role at POST /profile/role."
            )
        else:
            detail = f"{required_role} role required (account is '{actual_label}')."
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )

    return checker


require_student = require_role("student")
require_recruiter = require_role("recruiter")
