from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import init_db, close_db
from app.core.firebase import init_firebase
from app.core.langchain_setup import setup_langsmith

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    init_firebase()
    setup_langsmith()
    yield
    # Shutdown
    await close_db()

app = FastAPI(
    title="VERIF-AI API",
    description="AI Academic Profile & Skill Verification Backend",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "environment": settings.ENVIRONMENT}

@app.get("/")
async def root():
    return {
        "success": True, 
        "message": "Welcome to VERIF-AI API",
        "docs": "/docs"
    }

# V1 Routers to be included
# from app.api.v1 import auth, documents, analysis, profile, discover, verification
# app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
# app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
# app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["Analysis"])
# app.include_router(profile.router, prefix="/api/v1/profile", tags=["Profile"])
# app.include_router(discover.router, prefix="/api/v1/discover", tags=["Discovery"])
# app.include_router(verification.router, prefix="/api/v1/verification", tags=["Verification"])
