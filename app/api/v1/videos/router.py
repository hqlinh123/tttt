from fastapi import APIRouter

from app.api.v1.videos.controller import (
    # Runway
    generate_text_to_video,
    generate_image_to_video,
    generate_video_to_video,
    generate_video_with_references,
    generate_text_to_image,
    generate_image_to_image,

    # Existing Viterbox + Runway + FFmpeg flow
    generate_video,

    # Generated outputs
    get_generated_videos,
    get_generated_images,
)


router = APIRouter()

# ============================================================
# RUNWAY - TEXT -> VIDEO
# ============================================================

router.post(
    "/text-to-video"
)(
    generate_text_to_video
)


# ============================================================
# RUNWAY - IMAGE -> VIDEO
# ============================================================

router.post(
    "/image-to-video"
)(
    generate_image_to_video
)


# ============================================================
# RUNWAY - VIDEO -> VIDEO
# ============================================================

router.post(
    "/video-to-video"
)(
    generate_video_to_video
)


# ============================================================
# RUNWAY - VIDEO + REFERENCE IMAGES -> VIDEO
# ============================================================

router.post(
    "/video-to-video/references"
)(
    generate_video_with_references
)


# ============================================================
# RUNWAY - TEXT -> IMAGE
# ============================================================

router.post(
    "/text-to-image"
)(
    generate_text_to_image
)


# ============================================================
# RUNWAY - IMAGE + TEXT -> IMAGE
# ============================================================

router.post(
    "/image-to-image"
)(
    generate_image_to_image
)


# ============================================================
# EXISTING COMPLETE FLOW
#
# Viterbox voice
# +
# reference image(s)
# +
# Runway
# +
# FFmpeg
# ============================================================

router.post(
    "/generate"
)(
    generate_video
)


# ============================================================
# GENERATED VIDEOS
# ============================================================

router.get(
    "/"
)(
    get_generated_videos
)


# ============================================================
# GENERATED IMAGES
# ============================================================

router.get(
    "/images"
)(
    get_generated_images
)