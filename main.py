from app.core.config import init_firebase
from app.api.v1.auth import router as auth_router
from app.api.v1.profile import router as profile_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

init_firebase()

app = FastAPI(title="VerifAI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(profile_router)
