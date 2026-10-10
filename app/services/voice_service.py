# app/services/voice_service.py

import hashlib
import logging
import shutil
import subprocess
import time
import uuid
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional, List, Dict, Any, AsyncGenerator, BinaryIO

import edge_tts  # type: ignore
import librosa
import soundfile as sf
import torch
from fastapi import UploadFile, HTTPException, status, logger

from app.core.config.settings import WAVS_DIR, settings
from app.domain.constants.voices import AVAILABLE_VOICES
from app.domain.models.voices import TTSRequest, TTSResponse
from app.helpers.file_manager import FileManager
from app.infrastructure.repositories.audio_record_repository import AudioRecordRepository
from viterbox.tts import Viterbox

# Viterbox imports with proper error handling


logger = logging.getLogger(__name__)


class VoiceService:
    def __init__(self, voices_repository, config: dict = None):
        """
        Initialize VoiceService
        
        Args:
            voices_repository: Repository for voice operations
            config: Optional configuration dictionary
        """
        self.voices_repository = voices_repository
        
        # Default configuration
        if config is None:
            config = {}
        
        self.wavs_dir = Path(config.get("wavs_dir", "wavs"))
        self.upload_dir = Path(config.get("upload_dir", "uploads"))
        self.output_dir = Path(config.get("output_dir", "outputs"))
        self.temp_dir = Path(config.get("temp_dir", "temp"))
        self.device = config.get("device", "cpu")
        self.viterbox_available = config.get("viterbox_available", False)
        
        # Initialize Viterbox if available
        self.viterbox = None
        if self.viterbox_available:
            try:
                self.viterbox = Viterbox(device=self.device)
                logger.info(f"Viterbox initialized on {self.device}")
            except Exception as e:
                logger.error(f"Failed to initialize Viterbox: {e}")
                self.viterbox_available = False
        
        # Ensure directories exist
        for dir_path in [self.wavs_dir, self.upload_dir, self.output_dir, self.temp_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)


    def _api_path(self, path: str) -> str:
        """
        Add API prefix to public URL.

        Example:
            API_PREFIX=/api
            /wavs/thao.wav
            -> /api/wavs/thao.wav
        """
        prefix = getattr(settings, "API_PREFIX", "/api").rstrip("/")
        path = f"/{path.lstrip('/')}"

        return f"{prefix}{path}"
    # ==================== Private Helper Methods ====================
    
    def _get_audio_duration(self, file_path: Path) -> float:
        """Get audio duration in seconds"""
        try:
            y, sr = librosa.load(file_path, sr=None)
            return len(y) / sr
        except Exception as e:
            logger.warning(f"Could not get duration for {file_path}: {e}")
            return 0.0
    
    def _get_voice_display_name(self, filename: str) -> str:
        """Convert filename to display name"""
        name = Path(filename).stem
        name = name.replace("_", " ").replace("-", " ")
        return name.title()
    
    async def _convert_to_wav(self, file_path: Path) -> Path:
        """Convert audio file to WAV format"""
        if file_path.suffix.lower() == ".wav":
            return file_path
        
        try:
            wav_filename = file_path.stem + ".wav"
            wav_path = self.wavs_dir / wav_filename
            y, sr = librosa.load(file_path, sr=16000, mono=True)
            sf.write(wav_path, y, sr)
            # Remove original non-wav file
            file_path.unlink()
            return wav_path
        except Exception as e:
            logger.error(f"Conversion error for {file_path}: {e}")
            return file_path
    
    # ==================== Public API Methods ====================
    
    async def get_voices(self) -> dict:
        """Get all available voices with display names"""
        try:
            voices = []

            for file_path in self.wavs_dir.glob("*"):
                if file_path.suffix.lower() in [
                    ".wav",
                    ".mp3",
                    ".m4a",
                    ".flac",
                ]:
                    voices.append({
                        "id": file_path.name,
                        "name": self._get_voice_display_name(
                            file_path.name
                        ),
                        "filename": file_path.name,
                        "duration": round(
                            self._get_audio_duration(file_path),
                            2,
                        ),

                        # Public static URL
                        "url": self._api_path(
                            f"/wavs/{file_path.name}"
                        ),

                        # Download directly from static file
                        "download_url": self._api_path(
                            f"/wavs/{file_path.name}"
                        ),
                    })

            return {
                "success": True,
                "count": len(voices),
                "voices": voices,
                "viterbox_available": self.viterbox_available,
            }

        except Exception as e:
            logger.error(f"Error getting voices: {e}")

            raise HTTPException(
                status_code=500,
                detail=str(e),
            )
    async def download_voice(self, filename: str) -> dict:
        """Get voice file path for download"""
        # Security: Prevent path traversal attacks
        if ".." in filename or filename.startswith("/"):
            raise HTTPException(400, "Invalid filename")
        
        # Check in wavs directory
        file_path = self.wavs_dir / filename
        
        # Also check in uploads directory as fallback
        if not file_path.exists():
            file_path = self.upload_dir / filename
        
        if not file_path.exists():
            raise HTTPException(404, f"Voice file '{filename}' not found")
        
        # Get file extension for correct media type
        ext = file_path.suffix.lower()
        media_type = "audio/wav" if ext == ".wav" else "audio/mpeg"
        
        return {
            "file_path": file_path,
            "media_type": media_type,
            "filename": filename
        }
    
    async def upload_voice(self, file: UploadFile) -> dict:
        """Upload a new voice file"""
        # Validate extension
        allowed_extensions = [".wav", ".mp3", ".m4a", ".flac"]
        ext = Path(file.filename).suffix.lower()
        if ext not in allowed_extensions:
            raise HTTPException(400, f"Unsupported format. Allowed: {allowed_extensions}")
        
        # Validate size
        content = await file.read()
        if len(content) > 20 * 1024 * 1024:  # 20MB max
            raise HTTPException(400, "File too large. Max 20MB")
        
        # Generate a clean filename
        original_name = Path(file.filename).stem
        clean_name = "".join(c for c in original_name if c.isalnum() or c in "._- ").strip()
        clean_name = clean_name.lower().replace(" ", "_")
        
        # Ensure unique filename
        target_filename = f"{clean_name}{ext}"
        target_path = self.wavs_dir / target_filename
        
        counter = 1
        while target_path.exists():
            target_filename = f"{clean_name}_{counter}{ext}"
            target_path = self.wavs_dir / target_filename
            counter += 1
        
        # Save the uploaded file
        with open(target_path, "wb") as f:
            f.write(content)
        
        duration = self._get_audio_duration(target_path)
        display_name = self._get_voice_display_name(target_filename)
        
        return {
            "success": True,
            "message": "Voice file uploaded successfully",
            "voice": {
                "id": target_filename,
                "name": display_name,
                "filename": target_filename,
                "duration": round(duration, 2),
                "url": f"/wavs/{target_filename}",
                "download_url": f"/viterbox/voices/download/{target_filename}"
            },
            "file_path": target_path,
            "ext": ext
        }
    
    async def delete_voice(self, filename: str) -> dict:
        """Delete a voice file"""
        # Security: Prevent path traversal attacks
        if ".." in filename or filename.startswith("/"):
            raise HTTPException(400, "Invalid filename")
        
        file_path = self.wavs_dir / filename
        
        if not file_path.exists():
            file_path = self.upload_dir / filename
            if not file_path.exists():
                raise HTTPException(404, f"Voice file '{filename}' not found")
        
        # Delete the file
        file_path.unlink()
        
        # Also delete any associated converted files
        if file_path.suffix != ".wav":
            wav_path = file_path.with_suffix(".wav")
            if wav_path.exists():
                wav_path.unlink()
        
        return {
            "success": True,
            "message": f"Deleted voice file '{filename}'"
        }
    
    async def get_stats(self) -> dict:
        """Get service statistics"""
        output_files = list(self.output_dir.glob("*.wav"))
        upload_files = list(self.upload_dir.glob("*"))
        voice_files = list(self.wavs_dir.glob("*"))
        
        total_size = sum(f.stat().st_size for f in output_files) if output_files else 0
        voices_size = sum(f.stat().st_size for f in voice_files) if voice_files else 0
        
        return {
            "success": True,
            "viterbox_available": self.viterbox_available,
            "device": self.device if self.viterbox_available else None,
            "total_audio_files": len(output_files),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "uploaded_files": len(upload_files),
            "available_voices": len(voice_files),
            "voices_size_mb": round(voices_size / (1024 * 1024), 2)
        }
    
    # ==================== TTS Methods ====================
    
    async def text_to_speech(self, request: TTSRequest) -> TTSResponse:
        """Convert text to speech using available TTS engine"""
        if not self.viterbox_available or not self.viterbox:
            raise HTTPException(
                status_code=503,
                detail="TTS service not available. Viterbox not configured."
            )
        
        # Implementation would go here
        pass


    async def get_generated_voices(self) -> dict:
        """Get generated TTS audio files from output directory."""
        try:
            voices = []

            supported_extensions = {
                ".wav",
                ".mp3",
                ".m4a",
                ".flac",
            }

            for file_path in self.output_dir.iterdir():
                if (
                    not file_path.is_file()
                    or file_path.suffix.lower()
                    not in supported_extensions
                ):
                    continue

                stat = file_path.stat()

                voices.append({
                    "id": file_path.name,
                    "filename": file_path.name,
                    "duration": round(
                        self._get_audio_duration(file_path),
                        2,
                    ),
                    "audio_url": (
                        f"/viterbox/outputs/"
                        f"{file_path.name}"
                    ),
                    "created_at": datetime.fromtimestamp(
                        stat.st_mtime
                    ).isoformat(),
                })

            # newest first
            voices.sort(
                key=lambda item: item["created_at"],
                reverse=True,
            )

            return {
                "success": True,
                "count": len(voices),
                "voices": voices,
            }

        except Exception as e:
            logger.exception(
                "Failed to load generated voices"
            )

            raise HTTPException(
                status_code=500,
                detail=str(e),
            )