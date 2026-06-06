import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.api.auth import router as auth_router
from app.api.student import router as student_router
from app.api.recruiter import router as recruiter_router
from app.api.admin import router as admin_router
from app.middleware.logging_middleware import RequestLoggingMiddleware
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.utils.rate_limiter import rate_limit_middleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("verifai")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting VerifAI Backend...")
    yield
    logger.info("Shutting down VerifAI Backend...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(ErrorHandlerMiddleware)

app.middleware("http")(rate_limit_middleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

app.include_router(auth_router)
app.include_router(student_router)
app.include_router(recruiter_router)
app.include_router(admin_router)


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "service": settings.APP_NAME, "version": settings.APP_VERSION}
