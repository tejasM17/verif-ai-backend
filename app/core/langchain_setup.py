from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings
import os

def get_model(model_name: str = "gemini-1.5-pro", temperature: float = 0):
    """
    Returns a configured Gemini model instance.
    Defaulting to gemini-1.5-pro as specified in project tech stack (v2.5 ref).
    """
    return ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=settings.GEMINI_API_KEY,
        temperature=temperature,
    )

def setup_langsmith():
    if settings.LANGCHAIN_TRACING_V2 and settings.LANGCHAIN_API_KEY:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
        os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT
        print(f"LangSmith Tracing enabled: {settings.LANGCHAIN_PROJECT}")
