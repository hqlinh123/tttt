from typing import List

from fastapi import (
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)

from app.services.video_service import VideoService

from app.core.deps import (
    get_current_user,
    get_video_service,
)

from app.domain.models.user import User

# ============================================================
# RUNWAY
# ============================================================


# ============================================================
# 1. TEXT -> VIDEO
# RUNWAY
# ============================================================

async def generate_text_to_video(
    prompt: str = Form(...),
    style: str = Form("3d_cartoon"),
    aspect_ratio: str = Form("9:16"),
    duration: int = Form(5),
    video_service: VideoService = Depends(
        get_video_service
    ),
    current_user = Depends(get_current_user),
):
    """
    TEXT
      ↓
    Runway
      ↓
    video.mp4
    """

    return await video_service.generate_text_to_video(
        user_id=current_user.id,
        prompt=prompt,
        style=style,
        aspect_ratio=aspect_ratio,
        duration=duration,
    )


# ============================================================
# 2. IMAGE -> VIDEO
# RUNWAY
# ============================================================

async def generate_image_to_video(
    prompt: str = Form(""),
    style: str = Form("3d_cartoon"),
    aspect_ratio: str = Form("9:16"),
    duration: int = Form(5),

    # IMPORTANT:
    # use "images" instead of old single "image"
    images: List[UploadFile] = File(...),

    video_service: VideoService = Depends(
        get_video_service
    ),
     current_user = Depends(get_current_user),
):
    """
    IMAGE(S)
       +
    prompt
       ↓
    Runway
       ↓
    video.mp4

    Supports multiple uploaded images.
    """

    return await video_service.generate_image_to_video(
        user_id=current_user.id,
        images=images,
        prompt=prompt,
        style=style,
        aspect_ratio=aspect_ratio,
        duration=duration,
    )


# ============================================================
# 3. VIDEO -> VIDEO
# RUNWAY
# ============================================================

async def generate_video_to_video(
    prompt: str = Form(""),
    style: str = Form(""),
    aspect_ratio: str = Form("9:16"),

    video: UploadFile = File(...),

    video_service: VideoService = Depends(
        get_video_service
    ),
):
    """
    source video
         +
       prompt
         ↓
       Runway
         ↓
    new video
    """

    return await video_service.generate_video_to_video(
        video=video,
        prompt=prompt,
        style=style,
        aspect_ratio=aspect_ratio,
    )


# ============================================================
# 4. VIDEO + REFERENCE IMAGES -> VIDEO
# RUNWAY
# ============================================================

async def generate_video_with_references(
    prompt: str = Form(""),
    style: str = Form(""),
    aspect_ratio: str = Form("9:16"),

    video: UploadFile = File(...),

    images: List[UploadFile] = File(
        default=[]
    ),

    video_service: VideoService = Depends(
        get_video_service
    ),
):
    """
    source video
         +
    reference images
         +
       prompt
         ↓
       Runway
         ↓
    generated video
    """

    return await (
        video_service.generate_video_to_video(
            video=video,
            images=images,
            prompt=prompt,
            style=style,
            aspect_ratio=aspect_ratio,
        )
    )


# ============================================================
# 5. TEXT -> IMAGE
# RUNWAY
# ============================================================

async def generate_text_to_image(
    prompt: str = Form(...),
    style: str = Form("3d_cartoon"),
    aspect_ratio: str = Form("1:1"),

    video_service: VideoService = Depends(
        get_video_service
    ),
):
    """
    TEXT
      ↓
    Runway
      ↓
    image
    """

    return await video_service.generate_text_to_image(
        prompt=prompt,
        style=style,
        aspect_ratio=aspect_ratio,
    )


# ============================================================
# 6. IMAGE + TEXT -> IMAGE
# RUNWAY
# ============================================================

async def generate_image_to_image(
    prompt: str = Form(...),
    style: str = Form("3d_cartoon"),
    aspect_ratio: str = Form("1:1"),

    images: List[UploadFile] = File(...),

    video_service: VideoService = Depends(
        get_video_service
    ),
):
    """
    image(s)
       +
     prompt
       ↓
    Runway
       ↓
    image
    """

    return await video_service.generate_image_to_image(
        images=images,
        prompt=prompt,
        style=style,
        aspect_ratio=aspect_ratio,
    )


# ============================================================
# 7. OLD GENERATE VIDEO FLOW
#
# Viterbox voice
# +
# Runway image-to-video
# +
# FFmpeg
#
# Keep this for backward compatibility.
# ============================================================

async def generate_video(
    voice_url: str = Form(...),
    prompt: str = Form(""),
    style: str = Form("3d_cartoon"),
    aspect_ratio: str = Form("9:16"),

    # NEW
    # Multiple images supported
    images: List[UploadFile] = File(...),

    video_service: VideoService = Depends(
        get_video_service
    ),
):
    """
    Existing complete generation flow:

    Viterbox voice
          +
    reference image(s)
          +
        prompt
          ↓
        Runway
          ↓
      AI video
          +
    Viterbox voice
          ↓
       FFmpeg
          ↓
      final.mp4
    """

    return await video_service.generate_video(
        voice_url=voice_url,
        images=images,
        prompt=prompt,
        style=style,
        aspect_ratio=aspect_ratio,
    )


# ============================================================
# 8. GENERATED VIDEOS
# ============================================================

async def get_generated_videos(
    current_user = Depends(get_current_user),
    video_service: VideoService = Depends(
        get_video_service
    ),
):
    """
    Return generated videos from
    outputs/videos.
    """

    return await (
        video_service.get_generated_videos(user_id=current_user.id,)
    )


# ============================================================
# 9. GENERATED IMAGES
# ============================================================

async def get_generated_images(
    video_service: VideoService = Depends(
        get_video_service
    ),
):
    """
    Return generated images.
    """

    return await (
        video_service.get_generated_images()
    )