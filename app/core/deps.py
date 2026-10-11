from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import torch

from app.core.config import settings
from app.db.session import get_db
from app.core.security import decode_access_token
from app.infrastructure.repositories.audio_record_repository import AudioRecordRepository
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.repositories.token_repository import TokenRepository
from app.infrastructure.repositories.video_repository import VideoRepository
from app.infrastructure.repositories.voices_repository import VoicesRepository
from app.services.audio_upload_service import AudioUploadService
from app.services.auth_service import AuthService
from app.domain.models.user import User
from app.infrastructure.ai.video_generator import VideoGenerator
from app.services.email_service import EmailService
from app.services.tts_service import TTSService
from app.services.video_service import VideoService
from app.services.voice_service import VoiceService


# ================================
# OAuth2 (Bearer token)
# ================================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login"
)


# ================================
# VITERBOX - LAZY LOADING
# ================================

MODEL = None
DEVICE = None
VITERBOX_AVAILABLE = None

_model_lock = asyncio.Lock()


def get_device() -> str:
    if torch.cuda.is_available():
        return "cuda"

    # MPS only exists on supported PyTorch/platforms
    if (
        hasattr(torch.backends, "mps")
        and torch.backends.mps.is_available()
    ):
        return "mps"

    return "cpu"


async def get_viterbox_model():
    """
    Lazy load Viterbox.

    IMPORTANT:
    Model is NOT loaded during application startup.
    It is loaded only when a TTS request actually needs it.
    """
    global MODEL
    global DEVICE
    global VITERBOX_AVAILABLE

    if MODEL is not None:
        return MODEL, DEVICE, True

    async with _model_lock:
        # Another request may have loaded it while waiting for lock
        if MODEL is not None:
            return MODEL, DEVICE, True

        try:
            # Lazy import as well, so importing deps.py does not
            # initialize the Viterbox dependency chain.
            from viterbox import Viterbox

            VITERBOX_AVAILABLE = True
            DEVICE = get_device()

            print("=" * 50)
            print("✅ Viterbox is available")
            print(f"Device: {DEVICE}")
            print("⏳ Loading Viterbox model...")
            print("=" * 50)

            # from_pretrained() is synchronous/heavy.
            # Run it outside the event loop.
            MODEL = await asyncio.to_thread(
                Viterbox.from_pretrained,
                DEVICE,
            )

            print("=" * 50)
            print("✅ Viterbox model loaded!")
            print("=" * 50)

            return MODEL, DEVICE, True

        except ImportError as e:
            VITERBOX_AVAILABLE = False
            MODEL = None
            DEVICE = None

            print("=" * 50)
            print(f"⚠️ Viterbox not available: {e}")
            print("=" * 50)

            return None, None, False

        except Exception as e:
            VITERBOX_AVAILABLE = False
            MODEL = None

            print("=" * 50)
            print(f"⚠️ Failed to load Viterbox model: {e}")
            print("=" * 50)

            return None, DEVICE, False


# ================================
# CURRENT USER DEPENDENCY
# ================================

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
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

    return AuthService(
        user_repo,
        token_repo,
        email_service,
    )


async def get_voice_service(
    db: AsyncSession = Depends(get_db),
) -> VoiceService:
    """Dependency injection for voice service."""
    voices_repo = VoicesRepository(db)

    return VoiceService(voices_repo)


async def get_upload_service() -> AudioUploadService:
    """Dependency injection for audio upload service."""
    return AudioUploadService()


async def get_tts_service(
    db: AsyncSession = Depends(get_db),
) -> TTSService:
    """
    Dependency injection for TTS service.

    Viterbox is loaded here only when a TTS endpoint actually
    requests TTSService.
    """

    model, device, viterbox_available = await get_viterbox_model()

    tts_config = {
        "wavs_dir": settings.WAVS_DIR,
        "output_dir": settings.OUTPUT_DIR,
        "temp_dir": settings.TEMP_DIR,
        "upload_dir": settings.UPLOAD_DIR,

        "model": model,
        "device": device,
        "viterbox_available": viterbox_available,
    }

    voices_repo = VoicesRepository(db)

    return TTSService(
        voices_repo,
        tts_config,
    )


def get_video_service(
    db: AsyncSession = Depends(get_db),
) -> VideoService:
    video_repo = VideoRepository(db)

    return VideoService(
        video_repo=video_repo,
    )