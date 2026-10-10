# app/models/audio_record.py

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, Index
from sqlalchemy.sql import func
from datetime import datetime

from app.db.base import Base


class AudioRecord(Base):
    """Database model for TTS audio records"""
    
    __tablename__ = "audio_records"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # User information
    user_id = Column(String(255), nullable=True, index=True, comment="User ID who generated the audio")
    
    # Text content
    text = Column(Text, nullable=False, comment="Original input text")
    text_length = Column(Integer, nullable=False, comment="Length of input text")
    
    # Voice settings
    voice_id = Column(String(100), nullable=False, index=True, comment="Voice ID used for synthesis")
    voice_name = Column(String(100), nullable=True, comment="Voice display name")
    rate = Column(String(20), default="+0%", comment="Speech rate setting")
    volume = Column(String(20), default="+0%", comment="Volume setting")
    pitch = Column(String(20), default="+0Hz", comment="Pitch setting")
    
    # Voice cloning specific fields
    is_voice_cloning = Column(Boolean, default=False, comment="Whether voice cloning was used")
    speaker_wav = Column(String(500), nullable=True, comment="Path to speaker audio file for cloning")
    language = Column(String(10), default="vi", comment="Language code for voice cloning")
    
    # Audio file information
    audio_url = Column(String(500), nullable=False, comment="URL to access the audio file")
    filename = Column(String(255), unique=True, nullable=False, index=True, comment="Generated audio filename")
    duration_seconds = Column(Float, nullable=True, comment="Audio duration in seconds")
    file_size_bytes = Column(Integer, nullable=True, comment="Audio file size in bytes")
    
    # Metadata
    chunks_processed = Column(Integer, default=1, comment="Number of text chunks processed")
    from_cache = Column(Boolean, default=False, comment="Whether result came from cache")
    retry_count = Column(Integer, default=0, comment="Number of retry attempts")
    
    # Status
    status = Column(String(20), default="completed", comment="Status: pending, processing, completed, failed")
    error_message = Column(Text, nullable=True, comment="Error message if failed")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_user_created', 'user_id', 'created_at'),
        Index('idx_voice_created', 'voice_id', 'created_at'),
        Index('idx_status_created', 'status', 'created_at'),
    )
    
    def to_dict(self):
        """Convert model instance to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "text": self.text,
            "text_length": self.text_length,
            "voice_id": self.voice_id,
            "voice_name": self.voice_name,
            "rate": self.rate,
            "volume": self.volume,
            "pitch": self.pitch,
            "is_voice_cloning": self.is_voice_cloning,
            "speaker_wav": self.speaker_wav,
            "language": self.language,
            "audio_url": self.audio_url,
            "filename": self.filename,
            "duration_seconds": self.duration_seconds,
            "file_size_bytes": self.file_size_bytes,
            "chunks_processed": self.chunks_processed,
            "from_cache": self.from_cache,
            "retry_count": self.retry_count,
            "status": self.status,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f"<AudioRecord(id={self.id}, filename='{self.filename}', voice='{self.voice_id}')>"