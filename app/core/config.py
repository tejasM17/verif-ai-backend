import json
import os
import tempfile
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials

load_dotenv()


class Settings:
    FIREBASE_WEB_API_KEY: str = os.getenv("FIREBASE_WEB_API_KEY", "")
    FIREBASE_CRED_PATH: str = os.getenv("FIREBASE_CRED_PATH", "firebase-key.json")
    FIREBASE_CREDENTIALS_JSON: str | None = os.getenv("FIREBASE_CREDENTIALS_JSON")
    FIREBASE_DATABASE_URL: str = os.getenv("FIREBASE_DATABASE_URL", "")
    MONGODB_URI: str = os.getenv("MONGODB_URI", "")
    APP_TITLE: str = "VerifAI"
    APP_VERSION: str = "1.0.0"
    CORS_ORIGINS: str = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()


def _resolve_firebase_credentials():
    """Return a firebase_admin.credentials.Certificate, preferring the
    FIREBASE_CREDENTIALS_JSON env var when set (production), falling back to
    the FIREBASE_CRED_PATH file (local dev)."""
    if settings.FIREBASE_CREDENTIALS_JSON:
        try:
            data = json.loads(settings.FIREBASE_CREDENTIALS_JSON)
        except json.JSONDecodeError:
            # Tolerate escaped newlines that some secret stores add.
            data = json.loads(settings.FIREBASE_CREDENTIALS_JSON.replace("\\n", "\n"))
        return credentials.Certificate(data)
    return credentials.Certificate(settings.FIREBASE_CRED_PATH)


def init_firebase():
    if not firebase_admin._apps:
        cred = _resolve_firebase_credentials()
        options = {}
        if settings.FIREBASE_DATABASE_URL:
            options["databaseURL"] = settings.FIREBASE_DATABASE_URL
        firebase_admin.initialize_app(cred, options)