import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict

import firebase_admin
from firebase_admin import credentials, auth
from firebase_admin.auth import UserRecord

from app.config.settings import settings
from app.core.exceptions import UnauthorizedException

logger = logging.getLogger("verifai")

_SERVICE_ACCOUNT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "firebase-service-account.json",
)

if os.path.exists(_SERVICE_ACCOUNT_PATH):
    logger.info("Initializing Firebase Admin SDK from service account file: %s", _SERVICE_ACCOUNT_PATH)
    _cred = credentials.Certificate(_SERVICE_ACCOUNT_PATH)
else:
    logger.info("Initializing Firebase Admin SDK from environment variables. Project: %s", settings.FIREBASE_PROJECT_ID)
    _cred = credentials.Certificate(
        {
            "type": "service_account",
            "project_id": settings.FIREBASE_PROJECT_ID,
            "private_key_id": "3fd453162f42c94b6f855822ed38c58fe3c9b9a3",
            "private_key": settings.FIREBASE_PRIVATE_KEY,
            "client_email": settings.FIREBASE_CLIENT_EMAIL,
            "client_id": "118029264243849919913",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{settings.FIREBASE_CLIENT_EMAIL}",
            "universe_domain": "googleapis.com",
        }
    )

try:
    firebase_app = firebase_admin.initialize_app(_cred)
    logger.info("Firebase Admin SDK initialized successfully. Project: %s", settings.FIREBASE_PROJECT_ID)
except ValueError:
    firebase_app = firebase_admin.get_app()
    logger.info("Firebase Admin SDK already initialized. Project: %s", settings.FIREBASE_PROJECT_ID)


async def verify_firebase_token(id_token: str) -> Dict[str, Any]:
    server_now = datetime.now(timezone.utc)
    logger.info("Server time at token verification: %s (epoch=%.3f)", server_now.isoformat(), server_now.timestamp())

    if not id_token:
        logger.warning("verify_firebase_token called with empty token")
        raise UnauthorizedException("No Firebase token provided")

    try:
        decoded_token = auth.verify_id_token(id_token)

        token_iat = decoded_token.get("iat", 0)
        token_aud = decoded_token.get("aud", "")

        if token_aud != settings.FIREBASE_PROJECT_ID:
            logger.error(
                "Firebase project mismatch: token aud=%s, expected project=%s",
                token_aud, settings.FIREBASE_PROJECT_ID,
            )
            raise UnauthorizedException(
                "Firebase token was issued for a different project",
                error_code="FIREBASE_PROJECT_MISMATCH",
            )

        logger.info(
            "Firebase token verified successfully — uid=%s email=%s aud=%s iat=%s",
            decoded_token.get("uid"),
            decoded_token.get("email"),
            token_aud,
            datetime.fromtimestamp(token_iat, tz=timezone.utc).isoformat() if token_iat else "N/A",
        )
        return decoded_token

    except ValueError as e:
        err_str = str(e)
        if "Token used too early" in err_str:
            logger.error(
                "Token used too early (clock skew). Server time: %s (epoch=%.3f). "
                "Check server clock sync. Error: %s",
                server_now.isoformat(), server_now.timestamp(), err_str,
            )
            raise UnauthorizedException(
                "Firebase token used too early. Server clock may be out of sync.",
                error_code="TOKEN_USED_TOO_EARLY",
            )
        logger.error("Malformed Firebase token (ValueError): %s", err_str)
        raise UnauthorizedException(
            "Invalid Firebase token format",
            error_code="INVALID_FIREBASE_TOKEN",
        )
    except auth.ExpiredIdTokenError:
        logger.warning("Firebase token has expired")
        raise UnauthorizedException(
            "Firebase token has expired",
            error_code="TOKEN_EXPIRED",
        )
    except auth.InvalidIdTokenError as e:
        logger.error("Invalid Firebase token: %s", str(e))
        raise UnauthorizedException(
            "Invalid Firebase token",
            error_code="INVALID_FIREBASE_TOKEN",
        )
    except auth.RevokedIdTokenError:
        logger.warning("Firebase token has been revoked")
        raise UnauthorizedException(
            "Firebase token has been revoked",
            error_code="TOKEN_REVOKED",
        )
    except Exception as e:
        logger.error("Unexpected Firebase token verification error: %s", str(e), exc_info=True)
        raise UnauthorizedException(
            f"Token verification failed: {str(e)}",
            error_code="TOKEN_VERIFICATION_FAILED",
        )


async def get_firebase_user(firebase_uid: str) -> UserRecord:
    try:
        return auth.get_user(firebase_uid)
    except auth.UserNotFoundError:
        raise UnauthorizedException("Firebase user not found")
    except Exception as e:
        raise UnauthorizedException(f"Failed to get Firebase user: {str(e)}")


async def create_firebase_user(email: str, password: str) -> UserRecord:
    try:
        user = auth.create_user(
            email=email,
            password=password,
        )
        return user
    except auth.EmailAlreadyExistsError:
        raise UnauthorizedException("Email already registered in Firebase")
    except Exception as e:
        raise UnauthorizedException(f"Failed to create Firebase user: {str(e)}")


async def delete_firebase_user(firebase_uid: str) -> None:
    try:
        auth.delete_user(firebase_uid)
    except auth.UserNotFoundError:
        pass
    except Exception as e:
        raise UnauthorizedException(f"Failed to delete Firebase user: {str(e)}")


async def get_user_by_email(email: str) -> UserRecord:
    try:
        return auth.get_user_by_email(email)
    except auth.UserNotFoundError:
        raise UnauthorizedException("Firebase user not found")
    except Exception as e:
        raise UnauthorizedException(f"Failed to get Firebase user: {str(e)}")
