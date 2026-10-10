

from fastapi import APIRouter

from app.api.v1.auth.router import router as auth_router
from app.api.v1.videos.router import router as video_router
from app.api.v1.health.router import router as health_router
from app.api.v1.voices.router import router as voices_router
from app.api.v1.upload.router import router as upload_router

api_router = APIRouter()

# ---------------- Health ----------------
api_router.include_router(
    health_router,
    prefix="/health",
    tags=["Health"],
)

# ---------------- Auth ----------------
api_router.include_router(
    auth_router,
    prefix="/v1/auth",
    tags=["Auth"],
)

# ---------------- TTS Audio ----------------
api_router.include_router(
    voices_router,
    prefix="/v1/viterbox",
    tags=["TTS Audio"],
)

api_router.include_router(
    upload_router,
    prefix="/v1/upload",
    tags=["Upload"],
)

api_router.include_router(
    video_router,
    prefix="/v1/videos",
    tags=["Videos"],
)