from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "VerifAI Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/verifai"

    FIREBASE_PROJECT_ID: str = "verifai111"
    FIREBASE_PRIVATE_KEY: Optional[str] = None
    FIREBASE_CLIENT_EMAIL: str = "firebase-adminsdk-fbsvc@verifai111.iam.gserviceaccount.com"
    FIREBASE_API_KEY: str = "AIzaSyCw6yx5RnXQQDRkM39qdJKWedJtCXfBCWg"

    JWT_SECRET_KEY: str
    JWT_REFRESH_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    MONGODB_URL: str = "mongodb://verifai:verifai@ac-rhlsblf-shard-00-00.n8mdgy4.mongodb.net:27017,ac-rhlsblf-shard-00-01.n8mdgy4.mongodb.net:27017,ac-rhlsblf-shard-00-02.n8mdgy4.mongodb.net:27017/?ssl=true&replicaSet=atlas-ju8z1t-shard-0&authSource=admin&appName=Cluster0"
    MONGODB_DATABASE: str = "verifai"
    MONGODB_COLLECTION_PROFILE_IMAGES: str = "profile_images"

    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 10
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
