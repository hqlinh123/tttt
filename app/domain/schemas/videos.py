from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field
from pydantic.dataclasses import dataclass


# ============================================================
# ENUMS
# ============================================================

class GenerationType(str, Enum):
    TEXT_TO_VOICE = "text_to_voice"
    TEXT_TO_VIDEO = "text_to_video"
    IMAGE_TO_VIDEO = "image_to_video"
    VIDEO_TO_VIDEO = "video_to_video"
    VIDEO_REFERENCE_TO_VIDEO = "video_reference_to_video"
    TEXT_TO_IMAGE = "text_to_image"
    IMAGE_TO_IMAGE = "image_to_image"


class MediaType(str, Enum):
    AUDIO = "audio"
    VIDEO = "video"
    IMAGE = "image"


class MediaProvider(str, Enum):
    VITERBOX = "viterbox"
    RUNWAY = "runway"


class GenerationStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================================
# REQUEST MODELS
# ============================================================

class CreateVideoFromTextRequest(BaseModel):
    prompt: str
    style: str = ""
    aspect_ratio: str = "9:16"
    duration: int = 5


class CreateVideoFromImageRequest(BaseModel):
    image_url: Optional[str] = None
    image_urls: List[str] = Field(default_factory=list)

    prompt: str
    style: str = ""
    aspect_ratio: str = "9:16"
    duration: int = 5


class TextToVideoRequest(BaseModel):
    prompt: str
    style: str = ""
    aspect_ratio: str = "9:16"
    duration: int = 5


class TextToImageRequest(BaseModel):
    prompt: str
    style: str = ""
    aspect_ratio: str = "1:1"


# ============================================================
# COMMON DB / MEDIA RESPONSE
# ============================================================

class MediaRecordResponse(BaseModel):
    """
    Common response model for records stored in DB.

    Supports:
    - Text -> Voice
    - Text -> Video
    - Image -> Video
    - Video -> Video
    - Video + reference images -> Video
    - Text -> Image
    - Image -> Image
    """

    id: UUID
    user_id: Optional[UUID] = None

    generation_type: GenerationType
    media_type: MediaType
    provider: MediaProvider

    status: GenerationStatus = GenerationStatus.COMPLETED

    prompt: str = ""
    style: str = ""
    aspect_ratio: str = ""

    duration: float = 0

    output_url: Optional[str] = None
    output_filename: Optional[str] = None

    voice_url: Optional[str] = None

    source_video_url: Optional[str] = None

    source_image_url: Optional[str] = None
    source_image_urls: List[str] = Field(default_factory=list)

    reference_image_urls: List[str] = Field(default_factory=list)

    error_message: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================
# VIDEO RESPONSE
# ============================================================

class VideoGenerateResponse(BaseModel):
    success: bool = True
    message: str = "Video generated successfully"

    id: UUID
    filename: str
    video_url: str

    generation_type: Optional[GenerationType] = None

    provider: MediaProvider = MediaProvider.RUNWAY
    media_type: MediaType = MediaType.VIDEO
    status: GenerationStatus = GenerationStatus.COMPLETED

    voice_url: Optional[str] = None

    # Keep old field for backward compatibility
    image_url: Optional[str] = None

    # Multiple image support
    image_urls: List[str] = Field(default_factory=list)
    image_count: int = 0

    source_video_url: Optional[str] = None

    reference_image_urls: List[str] = Field(default_factory=list)
    reference_image_count: int = 0

    prompt: str = ""
    style: str = ""
    aspect_ratio: str = "9:16"

    duration: float = 0
    voice_duration: float = 0

    size: int = 0

    created_at: str


# ============================================================
# TEXT -> VIDEO RESPONSE
# ============================================================

class TextToVideoResponse(VideoGenerateResponse):
    generation_type: GenerationType = GenerationType.TEXT_TO_VIDEO


# ============================================================
# IMAGE -> VIDEO RESPONSE
# ============================================================

class ImageToVideoResponse(VideoGenerateResponse):
    generation_type: GenerationType = GenerationType.IMAGE_TO_VIDEO

    image_urls: List[str] = Field(default_factory=list)
    image_count: int = 0


# ============================================================
# VIDEO -> VIDEO RESPONSE
# ============================================================

class VideoToVideoResponse(VideoGenerateResponse):
    generation_type: GenerationType = GenerationType.VIDEO_TO_VIDEO

    source_video_url: Optional[str] = None


# ============================================================
# VIDEO + REFERENCE IMAGES -> VIDEO RESPONSE
# ============================================================

class VideoReferenceToVideoResponse(VideoGenerateResponse):
    generation_type: GenerationType = (
        GenerationType.VIDEO_REFERENCE_TO_VIDEO
    )

    source_video_url: Optional[str] = None

    reference_image_urls: List[str] = Field(default_factory=list)
    reference_image_count: int = 0


# ============================================================
# IMAGE RESPONSE
# ============================================================

class ImageGenerateResponse(BaseModel):
    success: bool = True
    message: str = "Image generated successfully"

    id: UUID
    filename: str
    image_url: str

    generation_type: Optional[GenerationType] = None

    provider: MediaProvider = MediaProvider.RUNWAY
    media_type: MediaType = MediaType.IMAGE
    status: GenerationStatus = GenerationStatus.COMPLETED

    prompt: str = ""
    style: str = ""
    aspect_ratio: str = "1:1"

    reference_image_urls: List[str] = Field(default_factory=list)
    reference_image_count: int = 0

    size: int = 0

    created_at: str


# ============================================================
# TEXT -> IMAGE RESPONSE
# ============================================================

class TextToImageResponse(ImageGenerateResponse):
    generation_type: GenerationType = GenerationType.TEXT_TO_IMAGE


# ============================================================
# IMAGE -> IMAGE RESPONSE
# ============================================================

class ImageToImageResponse(ImageGenerateResponse):
    generation_type: GenerationType = GenerationType.IMAGE_TO_IMAGE

    reference_image_urls: List[str] = Field(default_factory=list)
    reference_image_count: int = 0


# ============================================================
# VOICE RESPONSE
# ============================================================

class VoiceGenerateResponse(BaseModel):
    success: bool = True
    message: str = "Voice generated successfully"

    id: UUID
    filename: str
    audio_url: str

    generation_type: GenerationType = GenerationType.TEXT_TO_VOICE

    provider: MediaProvider = MediaProvider.VITERBOX
    media_type: MediaType = MediaType.AUDIO
    status: GenerationStatus = GenerationStatus.COMPLETED

    text: str = ""

    duration: float = 0
    size: int = 0

    created_at: str


# ============================================================
# LIST RESPONSES
# ============================================================

class GeneratedVideosResponse(BaseModel):
    success: bool = True
    count: int = 0
    videos: List[VideoGenerateResponse] = Field(default_factory=list)


class GeneratedImagesResponse(BaseModel):
    success: bool = True
    count: int = 0
    images: List[ImageGenerateResponse] = Field(default_factory=list)


class GeneratedVoicesResponse(BaseModel):
    success: bool = True
    count: int = 0
    voices: List[VoiceGenerateResponse] = Field(default_factory=list)


class MediaRecordsResponse(BaseModel):
    success: bool = True
    count: int = 0
    records: List[MediaRecordResponse] = Field(default_factory=list)


# ============================================================
# VIDEO SCENE
# ============================================================

@dataclass
class VideoScene:
    index: int
    start: float
    duration: int
    prompt: str

    video_path: Optional[Path] = None
    image_path: Optional[Path] = None

    image_url: Optional[str] = None
    video_url: Optional[str] = None


# ============================================================
# BACKWARD COMPATIBILITY
# ============================================================

VideoResponse = VideoGenerateResponse