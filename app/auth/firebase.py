import os
from typing import Any, Dict

import firebase_admin
from firebase_admin import credentials, auth
from firebase_admin.auth import UserRecord

from app.config.settings import settings
from app.core.exceptions import UnauthorizedException

_SERVICE_ACCOUNT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "firebase-service-account.json",
)

if os.path.exists(_SERVICE_ACCOUNT_PATH):
    _cred = credentials.Certificate(_SERVICE_ACCOUNT_PATH)
else:
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
except ValueError:
    firebase_app = firebase_admin.get_app()


async def verify_firebase_token(id_token: str) -> Dict[str, Any]:
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except auth.ExpiredIdTokenError:
        raise UnauthorizedException("Firebase token has expired")
    except auth.InvalidIdTokenError:
        raise UnauthorizedException("Invalid Firebase token")
    except auth.RevokedIdTokenError:
        raise UnauthorizedException("Firebase token has been revoked")
    except Exception as e:
        raise UnauthorizedException(f"Token verification failed: {str(e)}")


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
