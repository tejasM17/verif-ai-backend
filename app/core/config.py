from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
import json

class Settings(BaseSettings):
    # MongoDB
    MONGODB_URI: str
    MONGODB_DB_NAME: str = "verifai"

    # Firebase
    FIREBASE_PROJECT_ID: str
    FIREBASE_CREDENTIALS_JSON: str  # Expected as a JSON string

    # Google AI
    GEMINI_API_KEY: str
    GOOGLE_API_KEY: Optional[str] = None

    # LangSmith
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_API_KEY: Optional[str] = None
    LANGCHAIN_PROJECT: str = "verif-ai-hackathon"

    # External
    GITHUB_TOKEN: str
    BRAVE_API_KEY: Optional[str] = None

    # App
    ALLOWED_ORIGINS: str = "http://localhost:3000,https://verif-ai-frontend.vercel.app"
    PORT: int = 8000
    ENVIRONMENT: str = "development"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def firebase_creds(self) -> dict:
        try:
            return json.loads(self.FIREBASE_CREDENTIALS_JSON)
        except json.JSONDecodeError:
            # Fallback if it's already a dict or invalid
            return {}
    
    @property
    def origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

settings = Settings()
