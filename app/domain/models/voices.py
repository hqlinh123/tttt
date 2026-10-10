# app/domain/schemas/voice.py

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import re


class TTSRequest(BaseModel):
    """Request model for text-to-speech synthesis"""
    
    text: str = Field(
        ..., 
        min_length=1, 
        max_length=5000, 
        description="Text to convert to speech"
    )
    voice: str = Field(
        default="vi-VN-HoaiMyNeural", 
        description="Voice ID for speech synthesis"
    )
    rate: str = Field(
        default="+0%", 
        description="Speech rate (-50% to +50%)"
    )
    volume: str = Field(
        default="+0%", 
        description="Volume level (-50% to +50%)"
    )
    pitch: str = Field(
        default="+0Hz", 
        description="Pitch adjustment (-50Hz to +50Hz)"
    )
    
    # Voice cloning fields
    use_voice_cloning: bool = Field(
        default=False, 
        description="Enable voice cloning using XTTS"
    )
    speaker_wav: Optional[str] = Field(
        default=None, 
        description="Path to speaker audio file for voice cloning"
    )
    language: Optional[str] = Field(
        default="vi", 
        description="Language code for voice cloning (vi, en, es, fr, de, zh, ja, ko)"
    )
    
    # Metadata
    user_id: Optional[str] = Field(
        default=None, 
        description="User ID for tracking"
    )
    save_to_db: bool = Field(
        default=True, 
        description="Save audio record to database"
    )


class TTSResponse(BaseModel):
    """Response model for TTS synthesis"""
    
    success: bool = Field(..., description="Whether synthesis was successful")
    audio_url: Optional[str] = Field(None, description="URL to access the generated audio")
    message: str = Field(..., description="Status message")
    duration: Optional[float] = Field(None, description="Audio duration in seconds")
    filename: Optional[str] = Field(None, description="Generated audio filename")
    record_id: Optional[int] = Field(None, description="Database record ID")
    text_length: Optional[int] = Field(None, description="Length of input text")
    voice_cloning: bool = Field(False, description="Whether voice cloning was used")
    cached: bool = Field(False, description="Whether result came from cache")
    language: Optional[str] = Field(None, description="Language used for synthesis")
    chunks_processed: Optional[int] = Field(1, description="Number of text chunks processed")

class BatchTTSRequest(BaseModel):
    """Batch TTS request model"""
    
    requests: List[TTSRequest] = Field(
        ..., 
        min_length=1, 
        max_length=50, 
        description="List of TTS requests to process"
    )

class BatchTTSResponse(BaseModel):
    """Batch TTS response model"""
    
    results: List[Dict[str, Any]] = Field(..., description="List of individual results")
    total: int = Field(..., description="Total number of requests")
    successful: int = Field(..., description="Number of successful requests")
    failed: int = Field(0, description="Number of failed requests")
    total_duration: Optional[float] = Field(None, description="Total audio duration in seconds")

class VoiceInfo(BaseModel):
    """Voice information model"""
    
    id: str = Field(..., description="Unique voice identifier")
    name: str = Field(..., description="Display name of the voice")
    gender: str = Field(..., description="Voice gender (Male/Female)")
    locale: str = Field(..., description="Language locale code")
    locale_name: str = Field(..., description="Display name of the locale")
    style: Optional[str] = Field(None, description="Voice style (e.g., cheerful, newscast)")
    type: str = Field(default="edge_tts", description="TTS engine type (edge_tts/voice_cloning)")
    supports_languages: Optional[List[str]] = Field(None, description="Supported languages for voice cloning")
    requires_speaker_wav: Optional[bool] = Field(None, description="Whether voice requires speaker audio file")
    max_text_length: Optional[int] = Field(None, description="Maximum recommended text length")
    

class HealthResponse(BaseModel):
    """Health check response model"""
    
    status: str = Field(..., description="Service health status (healthy/degraded/unhealthy)")
    timestamp: str = Field(..., description="Current timestamp")
    audio_files_count: int = Field(..., description="Number of audio files in storage")
    version: str = Field(..., description="API version")
    details: Optional[Dict[str, Any]] = Field(None, description="Detailed health information")


class StatsResponse(BaseModel):
    """Service statistics response model"""
    
    total_audio_files: int = Field(..., description="Total number of audio files")
    total_storage_mb: float = Field(..., description="Total storage used in MB")
    available_voices: int = Field(..., description="Number of available voices")
    voices_by_locale: Dict[str, int] = Field(..., description="Voice count by locale")
    voice_cloning_enabled: bool = Field(False, description="Whether voice cloning is available")
    device: str = Field("cpu", description="Device used for processing (cpu/cuda)")
    cache_enabled: bool = Field(False, description="Whether caching is enabled")
    cache_stats: Optional[Dict[str, Any]] = Field(None, description="Cache statistics")
    max_concurrent_requests: int = Field(5, description="Maximum concurrent requests allowed")

class VoiceCloneRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    reference_audio_path: str = Field(..., description="Path to reference audio file")
    language: str = Field("vi")
    exaggeration: float = Field(0.5, ge=0.0, le=2.0)
    cfg_weight: float = Field(0.5, ge=0.0, le=1.0)
    temperature: float = Field(0.8, ge=0.1, le=1.0)
    sentence_pause_ms: int = Field(500, ge=0, le=2000)

class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    language: str = Field("vi", description="Language: vi, en, es, fr, de, zh, ja, ko")
    exaggeration: float = Field(0.5, ge=0.0, le=2.0)
    cfg_weight: float = Field(0.5, ge=0.0, le=1.0)
    temperature: float = Field(0.8, ge=0.1, le=1.0)
    sentence_pause_ms: int = Field(500, ge=0, le=2000, description="Pause between sentences (milliseconds)")
    voice: Optional[str] = Field(None, description="Voice file to use (optional)")

