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
        if current_user.get("role") != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"{required_role} role required",
            )
        return current_user

    return checker


require_student = require_role("student")
require_recruiter = require_role("recruiter")
