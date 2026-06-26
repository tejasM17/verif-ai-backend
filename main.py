from app.core.config import init_firebase, settings
from app.api.v1.auth import router as auth_router
from app.api.v1.profile import router as profile_router
from app.api.v1.resume import router as resume_router
from app.api.v1.companies import router as companies_router
from app.api.v1.applications import router as applications_router
from app.api.v1.jobs import router as jobs_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

init_firebase()

app = FastAPI(title="VerifAI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(resume_router)
app.include_router(companies_router)
app.include_router(applications_router)
app.include_router(jobs_router)