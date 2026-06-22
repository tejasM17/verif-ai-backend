import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials

load_dotenv()


class Settings:
    FIREBASE_WEB_API_KEY: str = os.getenv(
        "FIREBASE_WEB_API_KEY",
        "AIzaSyCw6yx5RnXQQDRkM39qdJKWedJtCXfBCWg",
    )
    FIREBASE_CRED_PATH: str = os.getenv("FIREBASE_CRED_PATH", "firebase-key.json")
    FIREBASE_DATABASE_URL: str = os.getenv("FIREBASE_DATABASE_URL", "")
    MONGODB_URI: str = os.getenv("MONGODB_URI", "")
    APP_TITLE: str = "VerifAI"
    APP_VERSION: str = "1.0.0"


settings = Settings()


def init_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate(settings.FIREBASE_CRED_PATH)
        options = {}
        if settings.FIREBASE_DATABASE_URL:
            options["databaseURL"] = settings.FIREBASE_DATABASE_URL
        firebase_admin.initialize_app(cred, options)
