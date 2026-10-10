# app/services/audio_upload_service.py

import logging
import os
import shutil
import hashlib
import uuid
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import aiofiles
import asyncio
import json

from app.core.config.settings import settings

logger = logging.getLogger(__name__)


class AudioUploadService:
    """Service for handling speaker audio uploads"""
    
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir = self.upload_dir / "metadata"
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
    
    async def save_audio_file(self, file, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Save uploaded audio file and prepare for voice cloning"""
        
        # Validate file type
        if not self._validate_file_type(file.filename):
            raise ValueError(f"Invalid file type. Allowed: {', '.join(settings.ALLOWED_AUDIO_FORMATS)}")
        
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # Validate file size
        if file_size > settings.MAX_SPEAKER_FILE_SIZE_MB * 1024 * 1024:
            raise ValueError(f"File too large. Max {settings.MAX_SPEAKER_FILE_SIZE_MB}MB")
        
        # Generate unique IDs
        original_filename = file.filename
        file_hash = hashlib.md5(content).hexdigest()
        speaker_id = str(uuid.uuid4())
        
        # Save original file
        original_filename_safe = f"{speaker_id}_{original_filename}"
        original_filepath = self.upload_dir / original_filename_safe
        
        async with aiofiles.open(original_filepath, 'wb') as f:
            await f.write(content)
        
        # Convert to WAV if needed
        wav_filename = f"{speaker_id}.wav"
        wav_filepath = self.upload_dir / wav_filename
        await self._convert_to_wav(original_filepath, wav_filepath)
        
        # Get duration and validate
        duration = await self._get_audio_duration(wav_filepath)
        
        if duration < 2:
            raise ValueError("Audio too short. Minimum 2 seconds recommended")
        
        if duration > 60:
            raise ValueError("Audio too long. Maximum 60 seconds")
        
        # Validate audio quality
        quality_status = await self._validate_audio_quality(wav_filepath)
        
        # Save metadata
        metadata = {
            "speaker_id": speaker_id,
            "original_filename": original_filename,
            "filename": wav_filename,
            "file_path": str(wav_filepath),
            "file_url": f"/api/v1/upload/speaker-audio/{speaker_id}/download",
            "duration": duration,
            "file_size": file_size,
            "user_id": user_id,
            "file_hash": file_hash,
            "created_at": datetime.now().isoformat(),
            "quality_status": quality_status,
            "name": None,
            "description": None,
            "tags": [],
            "usage_count": 0
        }
        
        await self._save_metadata(speaker_id, metadata)
        
        # Clean up original file
        if original_filepath != wav_filepath:
            original_filepath.unlink()
        
        return metadata
    
    async def _convert_to_wav(self, input_path: Path, output_path: Path):
        """Convert audio file to WAV format"""
        try:
            cmd = [
                'ffmpeg',
                '-i', str(input_path),
                '-acodec', 'pcm_s16le',
                '-ac', '1',  # Mono
                '-ar', '16000',  # 16kHz
                '-y',  # Overwrite
                str(output_path)
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"FFmpeg conversion failed: {stderr.decode()}")
                
        except Exception as e:
            raise ValueError(f"Audio conversion failed: {str(e)}")
    
    async def _get_audio_duration(self, filepath: Path) -> float:
        """Get audio duration in seconds"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                str(filepath)
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, _ = await process.communicate()
            duration = float(stdout.decode().strip())
            return duration
            
        except Exception as e:
            logger.warning(f"Failed to get duration: {e}")
            return 0.0
    
    async def _validate_audio_quality(self, filepath: Path) -> Dict[str, Any]:
        """Validate audio quality for voice cloning"""
        try:
            # Get audio info
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-select_streams', 'a:0',
                '-show_entries', 'stream=sample_rate,channels',
                '-of', 'default=noprint_wrappers=1',
                str(filepath)
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, _ = await process.communicate()
            output = stdout.decode()
            
            sample_rate = None
            channels = None
            
            for line in output.split('\n'):
                if 'sample_rate' in line:
                    sample_rate = line.split('=')[1]
                if 'channels' in line:
                    channels = int(line.split('=')[1])
            
            quality_status = {
                "is_good": True,
                "sample_rate": int(sample_rate) if sample_rate else None,
                "channels": channels,
                "warnings": []
            }
            
            if sample_rate and int(sample_rate) < 16000:
                quality_status["is_good"] = False
                quality_status["warnings"].append(f"Low sample rate: {sample_rate}Hz (recommended: 16000Hz)")
            
            if channels and channels != 1:
                quality_status["warnings"].append("Audio should be mono (converted automatically)")
            
            return quality_status
            
        except Exception as e:
            return {"is_good": False, "warnings": [str(e)]}
    
    def _validate_file_type(self, filename: str) -> bool:
        """Validate file extension"""
        ext = Path(filename).suffix.lower()
        return ext in settings.ALLOWED_AUDIO_FORMATS
    
    async def _save_metadata(self, speaker_id: str, metadata: Dict[str, Any]):
        """Save metadata to JSON file"""
        metadata_file = self.metadata_dir / f"{speaker_id}.json"
        async with aiofiles.open(metadata_file, 'w') as f:
            await f.write(json.dumps(metadata, indent=2))
    
    async def get_speaker_info(self, speaker_id: str) -> Optional[Dict[str, Any]]:
        """Get speaker information by ID"""
        metadata_file = self.metadata_dir / f"{speaker_id}.json"
        if not metadata_file.exists():
            return None
        
        async with aiofiles.open(metadata_file, 'r') as f:
            content = await f.read()
            metadata = json.loads(content)
            
            # Increment usage count
            metadata["usage_count"] = metadata.get("usage_count", 0) + 1
            await self._save_metadata(speaker_id, metadata)
            
            return metadata
    
    async def get_speaker_file_path(self, speaker_id: str) -> Optional[Path]:
        """Get speaker audio file path"""
        info = await self.get_speaker_info(speaker_id)
        if info:
            return Path(info["file_path"])
        return None
    
    async def delete_speaker_audio(self, speaker_id: str) -> bool:
        """Delete speaker audio file and metadata"""
        info = await self.get_speaker_info(speaker_id)
        if not info:
            return False
        
        # Delete audio file
        audio_path = Path(info["file_path"])
        if audio_path.exists():
            audio_path.unlink()
        
        # Delete metadata
        metadata_file = self.metadata_dir / f"{speaker_id}.json"
        if metadata_file.exists():
            metadata_file.unlink()
        
        return True
    
    async def list_speaker_audios(
        self, 
        user_id: Optional[str] = None, 
        limit: int = 50, 
        offset: int = 0
    ) -> Dict[str, Any]:
        """List all speaker audio files"""
        speakers = []
        metadata_files = list(self.metadata_dir.glob("*.json"))
        
        for metadata_file in metadata_files:
            async with aiofiles.open(metadata_file, 'r') as f:
                content = await f.read()
                speaker = json.loads(content)
                
                if user_id and speaker.get("user_id") != user_id:
                    continue
                
                speakers.append(speaker)
        
        # Sort by created_at (newest first)
        speakers.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        total = len(speakers)
        speakers = speakers[offset:offset + limit]
        
        return {
            "total": total,
            "speakers": speakers
        }
    
    async def update_speaker_info(
        self, 
        speaker_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Update speaker information"""
        info = await self.get_speaker_info(speaker_id)
        if not info:
            return None
        
        if name:
            info["name"] = name
        if description:
            info["description"] = description
        if tags:
            info["tags"] = tags.split(",") if isinstance(tags, str) else tags
        
        info["updated_at"] = datetime.now().isoformat()
        
        await self._save_metadata(speaker_id, info)
        return info
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics about speaker audio files"""
        metadata_files = list(self.metadata_dir.glob("*.json"))
        
        total_speakers = len(metadata_files)
        total_duration = 0
        total_size = 0
        quality_good = 0
        
        for metadata_file in metadata_files:
            async with aiofiles.open(metadata_file, 'r') as f:
                content = await f.read()
                speaker = json.loads(content)
                
                total_duration += speaker.get("duration", 0)
                total_size += speaker.get("file_size", 0)
                
                if speaker.get("quality_status", {}).get("is_good", False):
                    quality_good += 1
        
        return {
            "total_speakers": total_speakers,
            "total_duration_seconds": total_duration,
            "total_duration_minutes": total_duration / 60,
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "quality_good_count": quality_good,
            "quality_good_percentage": (quality_good / total_speakers * 100) if total_speakers > 0 else 0
        }