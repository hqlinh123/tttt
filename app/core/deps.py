from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
import torch

from app.core.config import settings
from app.db.session import get_db
from app.core.security import decode_access_token
from app.infrastructure.repositories.audio_record_repository import AudioRecordRepository
from app.infrastructure.repositories.user_repository import (
    UserRepository,
)
from app.infrastructure.repositories.token_repository import (
    TokenRepository,
)
from app.infrastructure.repositories.video_repository import VideoRepository
from app.infrastructure.repositories.voices_repository import VoicesRepository
from app.services.audio_upload_service import AudioUploadService
from app.services.auth_service import AuthService
from app.domain.models.user import User
from app.infrastructure.ai.video_generator import (
    VideoGenerator
)
from app.services.email_service import EmailService
from app.services.tts_service import TTSService
from app.services.video_service import VideoService
from app.services.voice_service import VoiceService
from viterbox.tts import Viterbox

# ================================
# OAuth2 (Bearer token)
# ================================
VITERBOX_AVAILABLE: bool = False

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login"
)

VITERBOX_AVAILABLE = False
try:
    from viterbox import Viterbox
    VITERBOX_AVAILABLE = True
    print("=" * 50)
    print("✅ Viterbox is available")
    print("=" * 50)
except ImportError:
    VITERBOX_AVAILABLE = False
    print("=" * 50)
    print("⚠️ Viterbox not available. Install: https://github.com/iamdinhthuan/viterbox-tts.git")
    print("=" * 50)

if VITERBOX_AVAILABLE:
            if torch.cuda.is_available():
                DEVICE = "cuda"
            elif torch.backends.mps.is_available():
                DEVICE = "mps"
            else:
                DEVICE = "cpu"

            print(f"Device: {DEVICE}")

            try:
                MODEL = Viterbox.from_pretrained(DEVICE)
                print("✅ Model loaded!")
            except Exception as e:
                MODEL = None
                viterbox_available = False
                print(f"⚠️ Failed to load model: {e}")
else:
            MODEL = None
            print("⚠️ Viterbox not installed. Voice cloning will not work.")

# ================================
# CURRENT USER DEPENDENCY
# ================================

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        # payload = decode_access_token(token)
        payload = decode_access_token(token)
        sub = payload.get("sub")
        if sub is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing subject",
            )

        user_id = sub

        user_repo = UserRepository(db)
        user = await user_repo.get_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        return user

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


# ================================
# SERVICES DI
# ================================

def get_auth_service(
    db: AsyncSession = Depends(get_db),
) -> AuthService:
    user_repo = UserRepository(db)
    token_repo = TokenRepository(db)
    email_service = EmailService()
    return AuthService(user_repo, token_repo, email_service)

async def get_voice_service(db: AsyncSession = Depends(get_db),) -> VoiceService:
    """Dependency injection for voice service"""
    try:
        voices_repo = VoicesRepository(db)
        voice_service = VoiceService(voices_repo)
        return voice_service
    finally:
        await db.close()
async def get_upload_service() -> AudioUploadService:
    """Dependency injection for audio upload service"""
    return AudioUploadService()

async def get_tts_service(db: AsyncSession = Depends(get_db),) -> TTSService:
    """Dependency injection for TTS service"""
    viterbox_available = VITERBOX_AVAILABLE
    model = MODEL if viterbox_available else None
    device = DEVICE if viterbox_available else None
    try:
        

        print("=" * 50)
        tts_config = {
            "wavs_dir": settings.WAVS_DIR,
            "output_dir": settings.OUTPUT_DIR,
            "temp_dir": settings.TEMP_DIR,
            "upload_dir": settings.UPLOAD_DIR,
            "model": model,
             # Add any other config options your TTSService needs
             # For example, if you want to pass the device info:
             "device": device,
             "viterbox_available": viterbox_available
            # Add any other config options your TTSService needs
        }
        voices_repo = VoicesRepository(db)
        tts_service = TTSService(voices_repo, tts_config)
        return tts_service
    finally:
        await db.close()
def get_video_service(
    db: AsyncSession = Depends(get_db),
) -> VideoService:
    video_repo = VideoRepository(db)

    return VideoService(
        video_repo=video_repo,
    )