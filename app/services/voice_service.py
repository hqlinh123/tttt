# app/services/voice_service.py
import logging
import uuid
from datetime import datetime
from pathlib import Path

import librosa
import soundfile as sf
from fastapi import UploadFile, HTTPException, status, logger

from app.core.config.settings import WAVS_DIR, settings
from app.domain.constants.voices import AVAILABLE_VOICES
from app.domain.models.voices import TTSRequest, TTSResponse
from app.helpers.file_manager import FileManager
from app.infrastructure.repositories.audio_record_repository import AudioRecordRepository

# Viterbox imports with proper error handling


logger = logging.getLogger(__name__)


class VoiceService:
    def __init__(
        self,
        voices_repository,
        config: dict = None,
    ):
        """
        Initialize VoiceService.

        IMPORTANT:
        VoiceService does NOT import or initialize Viterbox.

        Viterbox model must be lazy-loaded externally and injected
        through config["model"] when required.
        """

        self.voices_repository = voices_repository

        if config is None:
            config = {}

        # Directories
        self.wavs_dir = Path(
            config.get(
                "wavs_dir",
                "wavs",
            )
        )

        self.upload_dir = Path(
            config.get(
                "upload_dir",
                "uploads",
            )
        )

        self.output_dir = Path(
            config.get(
                "output_dir",
                "outputs",
            )
        )

        self.temp_dir = Path(
            config.get(
                "temp_dir",
                "temp",
            )
        )

        # Viterbox configuration
        #
        # IMPORTANT:
        # Do NOT create Viterbox here.
        self.viterbox = config.get("model")

        self.device = config.get(
            "device"
        )

        self.viterbox_available = (
            self.viterbox is not None
        )

        # Ensure directories exist
        for dir_path in [
            self.wavs_dir,
            self.upload_dir,
            self.output_dir,
            self.temp_dir,
        ]:
            dir_path.mkdir(
                parents=True,
                exist_ok=True,
            )

        if self.viterbox_available:
            logger.info(
                "VoiceService initialized with "
                "Viterbox model on %s",
                self.device,
            )
        else:
            logger.debug(
                "VoiceService initialized without "
                "Viterbox model"
            )

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
    
    async def text_to_speech(
    self,
    request: TTSRequest,
) -> TTSResponse:
        """
        Convert text to speech using injected Viterbox model.
        """

        if self.viterbox is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "TTS service not available. "
                    "Viterbox model has not been loaded."
                ),
            )

        try:
            import asyncio

            ref_audio = getattr(
                request,
                "voice",
                None,
            )

            if ref_audio:
                ref_path = Path(ref_audio)

                if not ref_path.exists():
                    wav_path = (
                        self.wavs_dir
                        / ref_audio
                    )

                    upload_path = (
                        self.upload_dir
                        / ref_audio
                    )

                    if wav_path.exists():
                        ref_path = wav_path

                    elif upload_path.exists():
                        ref_path = upload_path

                    else:
                        raise HTTPException(
                            status_code=404,
                            detail=(
                                f"Reference voice "
                                f"'{ref_audio}' not found"
                            ),
                        )

                ref_audio = str(ref_path)

            wav = await asyncio.to_thread(
                self.viterbox.generate,
                text=request.text,
                language=request.language,
                audio_prompt=ref_audio,
                exaggeration=request.exaggeration,
                cfg_weight=request.cfg_weight,
                temperature=request.temperature,
                sentence_pause_ms=request.sentence_pause_ms,
            )

            if hasattr(wav, "cpu"):
                audio_np = (
                    wav[0]
                    .cpu()
                    .numpy()
                )

            elif isinstance(
                wav,
                (list, tuple),
            ):
                item = wav[0]

                if hasattr(item, "cpu"):
                    audio_np = (
                        item
                        .cpu()
                        .numpy()
                    )
                else:
                    audio_np = item

            else:
                audio_np = wav

            audio_np, _ = librosa.effects.trim(
                audio_np,
                top_db=30,
            )

            filename = (
                f"{uuid.uuid4().hex}.wav"
            )

            output_path = (
                self.output_dir
                / filename
            )

            sample_rate = getattr(
                self.viterbox,
                "sr",
                24000,
            )

            sf.write(
                output_path,
                audio_np,
                sample_rate,
            )

            duration = (
                len(audio_np)
                / sample_rate
            )

            return {
                "success": True,
                "message": "Generated successfully",
                "audio_url": self._api_path(
                    f"/viterbox/outputs/{filename}"
                ),
                "filename": filename,
                "duration": round(
                    duration,
                    2,
                ),
                "text_length": len(
                    request.text
                ),
                "language": request.language,
                "voice_cloning": bool(
                    ref_audio
                ),
                "voice_used": (
                    Path(ref_audio).name
                    if ref_audio
                    else None
                ),
            }

        except HTTPException:
            raise

        except Exception as e:
            logger.exception(
                "Viterbox TTS generation failed"
            )

            raise HTTPException(
                status_code=500,
                detail=str(e),
            )


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