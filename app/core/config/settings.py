# app/core/config/settings.py

import os
import tempfile

from pydantic import Field, validator
from typing import List, Optional
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

os.environ["GRADIO_TEMP_DIR"] = tempfile.gettempdir() + "/my_gradio_tmp"
os.makedirs(os.environ["GRADIO_TEMP_DIR"], exist_ok=True)

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

VIDEO_DIR = OUTPUT_DIR / "videos"
VIDEO_IMAGE_DIR = OUTPUT_DIR / "video-images"

VIDEO_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

VIDEO_IMAGE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

WAVS_DIR = Path("wavs")
WAVS_DIR.mkdir(exist_ok=True)

class Settings(BaseSettings):
    """Application settings for AI Video Backend with TTS Service"""
    
    # App Settings
    APP_NAME: str = Field(default="AI Video Backend", env="APP_NAME")
    APP_VERSION: str = Field(default="1.0.0", env="APP_VERSION")
    ENVIRONMENT: str = Field(default="dev", env="ENVIRONMENT")
    
    # API Settings
    ENABLE_DOCS: bool = Field(default=True, env="ENABLE_DOCS")
    API_PREFIX: str = Field(default="/api/v1", env="API_PREFIX")
    
    # CORS Settings
    CORS_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:19006",
            "http://127.0.0.1:8000",
            "*",  # DEV ONLY
        ],
        env="CORS_ORIGINS"
    )

    DATABASE_URL: str = "postgresql://neondb_owner:npg_gNuY7hMQFmx9@ep-weathered-hall-b8laxa9w-pooler.c-14.us-east-1.aws.neon.tech/neondb"

    JWT_SECRET: str = "CHANGE_ME"
    JWT_ALGORITHM: str = "HS256"
    JWT_ISSUER: str = "auth.ai-video.app"

    # ✅ ADD missing fields (fix crash)
    JWT_AUDIENCE: Optional[str] = None
    REPLICATE_API_KEY: Optional[str] = None
    REPLICATE_WEBHOOK_KEY: Optional[str] = None
    REPLICATE_MODEL_VERSION: Optional[str] = None

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_SERVER: str = "mail server"
    MAIL_PORT: int = 587

    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = False
    VALIDATE_CERTS: bool = False
    RUNWAYML_API_SECRET: str = ""
    RUNWAY_VIDEO_MODEL: str = "gen4.5"
    RUNWAY_REFERENCE_VIDEO_MODEL: str = "seedance2_5"
    RUNWAY_IMAGE_MODEL: str = "gen4_image"

    # ✅ Pydantic v2 config
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="forbid",  # keep strict (recommended)
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # JWT Settings
    JWT_SECRET: str = Field(default="CHANGE_ME", env="JWT_SECRET")
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    JWT_ISSUER: str = Field(default="auth.ai-video.app", env="JWT_ISSUER")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=30, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # Database Settings
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:admin@localhost:5432/postgres",
        env="DATABASE_URL"
    )
    DATABASE_POOL_SIZE: int = Field(default=10, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(default=20, env="DATABASE_MAX_OVERFLOW")
    SQL_ECHO: bool = Field(default=False, env="SQL_ECHO")
    
    # TTS Settings
    MAX_TEXT_LENGTH: int = Field(default=5000, env="MAX_TEXT_LENGTH")
    AUDIO_DIR: str = Field(default="audio_files", env="AUDIO_DIR")
    MAX_AUDIO_AGE_HOURS: int = Field(default=24, env="MAX_AUDIO_AGE_HOURS")
    
    # Voice Cloning Settings
    USE_XTTS_VIETNAMESE: bool = Field(default=True, env="USE_XTTS_VIETNAMESE")
    ENABLE_VOICE_CLONING: bool = Field(default=True, env="ENABLE_VOICE_CLONING")
    
    # Cache Settings
    CACHE_ENABLED: bool = Field(default=True, env="CACHE_ENABLED")
    CACHE_DIR: str = Field(default="cache/tts", env="CACHE_DIR")
    MAX_CACHE_SIZE_MB: int = Field(default=1000, env="MAX_CACHE_SIZE_MB")
    MAX_CACHE_AGE_HOURS: int = Field(default=24, env="MAX_CACHE_AGE_HOURS")
    
    # Performance Settings
    TTS_CONCURRENT_LIMIT: int = Field(default=5, env="TTS_CONCURRENT_LIMIT")
    TTS_REQUEST_TIMEOUT: int = Field(default=60, env="TTS_REQUEST_TIMEOUT")
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = Field(default=60, env="RATE_LIMIT_REQUESTS")
    RATE_LIMIT_WINDOW_SECONDS: int = Field(default=60, env="RATE_LIMIT_WINDOW_SECONDS")
    
    # Feature Flags
    ENABLE_BATCH_PROCESSING: bool = Field(default=True, env="ENABLE_BATCH_PROCESSING")
    ENABLE_STREAMING: bool = Field(default=True, env="ENABLE_STREAMING")
    
    # File Upload Settings
    MAX_SPEAKER_FILE_SIZE_MB: int = Field(default=10, env="MAX_SPEAKER_FILE_SIZE_MB")
    ALLOWED_AUDIO_FORMATS: List[str] = Field(
        default=[".wav", ".mp3", ".m4a", ".flac"],
        env="ALLOWED_AUDIO_FORMATS"
    )

    UPLOAD_DIR: str = "uploads/speaker_audio"
    MAX_UPLOAD_DURATION_SECONDS: int = 30  # Max 30 seconds
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FILE: Optional[str] = Field(default=None, env="LOG_FILE")
    
    # Redis (optional, for distributed caching)
    REDIS_URL: Optional[str] = Field(default=None, env="REDIS_URL")
    
# Create settings instance
settings = Settings()
