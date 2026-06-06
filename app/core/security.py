import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Dict

from jose import JWTError, jwt, ExpiredSignatureError

from app.config.settings import settings
from app.core.exceptions import UnauthorizedException

logger = logging.getLogger("verifai")


def create_access_token(
    user_id: str,
    firebase_uid: str,
    email: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    now = datetime.now(timezone.utc)
    to_encode: Dict[str, Any] = {
        "sub": user_id,
        "firebase_uid": firebase_uid,
        "email": email,
        "role": role,
        "type": "access",
    }
    expire = now + (
        expires_delta
        if expires_delta
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode["exp"] = expire
    to_encode["iat"] = now
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(
    user_id: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    now = datetime.now(timezone.utc)
    to_encode: Dict[str, Any] = {
        "sub": user_id,
        "role": role,
        "type": "refresh",
    }
    expire = now + (
        expires_delta
        if expires_delta
        else timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    to_encode["exp"] = expire
    to_encode["iat"] = now
    return jwt.encode(to_encode, settings.JWT_REFRESH_SECRET, algorithm=settings.JWT_ALGORITHM)


def verify_access_token(token: str) -> Dict[str, Any]:
    server_now = datetime.now(timezone.utc)
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("type") != "access":
            logger.warning(
                "Invalid JWT type: expected 'access', got '%s'. Server: %s (epoch=%.3f)",
                payload.get("type"), server_now.isoformat(), server_now.timestamp(),
            )
            raise UnauthorizedException(
                "Invalid token type",
                error_code="INVALID_TOKEN_TYPE",
            )
        return payload
    except ExpiredSignatureError:
        logger.warning(
            "Access token expired. Server: %s (epoch=%.3f)",
            server_now.isoformat(), server_now.timestamp(),
        )
        raise UnauthorizedException(
            "Access token has expired",
            error_code="ACCESS_TOKEN_EXPIRED",
        )
    except JWTError as e:
        logger.warning(
            "Invalid access token: %s. Server: %s (epoch=%.3f)",
            str(e), server_now.isoformat(), server_now.timestamp(),
        )
        raise UnauthorizedException(
            "Invalid access token",
            error_code="INVALID_ACCESS_TOKEN",
        )


def verify_refresh_token(token: str) -> Dict[str, Any]:
    server_now = datetime.now(timezone.utc)
    try:
        payload = jwt.decode(
            token, settings.JWT_REFRESH_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("type") != "refresh":
            logger.warning(
                "Invalid JWT type: expected 'refresh', got '%s'. Server: %s (epoch=%.3f)",
                payload.get("type"), server_now.isoformat(), server_now.timestamp(),
            )
            raise UnauthorizedException(
                "Invalid token type",
                error_code="INVALID_TOKEN_TYPE",
            )
        return payload
    except ExpiredSignatureError:
        logger.warning(
            "Refresh token expired. Server: %s (epoch=%.3f)",
            server_now.isoformat(), server_now.timestamp(),
        )
        raise UnauthorizedException(
            "Refresh token has expired",
            error_code="REFRESH_TOKEN_EXPIRED",
        )
    except JWTError as e:
        logger.warning(
            "Invalid refresh token: %s. Server: %s (epoch=%.3f)",
            str(e), server_now.isoformat(), server_now.timestamp(),
        )
        raise UnauthorizedException(
            "Invalid refresh token",
            error_code="INVALID_REFRESH_TOKEN",
        )
