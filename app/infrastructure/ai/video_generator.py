import time
from dataclasses import dataclass
from uuid import uuid4
from pathlib import Path
from typing import Optional


# ================================
# Result object
# ================================

@dataclass
class VideoGenerationResult:
    video_url: str
    thumbnail_url: Optional[str] = None


# ================================
# Video Generator
# ================================

class VideoGenerator:
    """
    Abstraction for AI video generation.
    Can be replaced by:
    - Stable Diffusion + AnimateDiff
    - Sora API
    - Runway API
    - Local ffmpeg pipeline
    """

    OUTPUT_DIR = Path("storage/videos")

    def __init__(self):
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ---------------- TEXT → VIDEO ----------------
    def generate_from_text(
        self,
        prompt: str,
        style: Optional[str] = None,
    ) -> VideoGenerationResult:
        """
        Fake generation for now (simulate heavy AI work)
        """
        time.sleep(3)  # simulate GPU work

        video_id = str(uuid4())
        video_path = self.OUTPUT_DIR / f"{video_id}.mp4"
        thumbnail_path = self.OUTPUT_DIR / f"{video_id}.jpg"

        # create fake files
        video_path.write_bytes(b"FAKE_VIDEO_CONTENT")
        thumbnail_path.write_bytes(b"FAKE_THUMBNAIL")

        return VideoGenerationResult(
            video_url=f"/static/videos/{video_path.name}",
            thumbnail_url=f"/static/videos/{thumbnail_path.name}",
        )

    # ---------------- IMAGE → VIDEO ----------------
    def generate_from_image(
        self,
        image_url: str,
        prompt: Optional[str] = None,
    ) -> VideoGenerationResult:
        """
        Fake image-to-video generation
        """
        time.sleep(3)

        video_id = str(uuid4())
        video_path = self.OUTPUT_DIR / f"{video_id}.mp4"

        video_path.write_bytes(b"FAKE_VIDEO_FROM_IMAGE")

        return VideoGenerationResult(
            video_url=f"/static/videos/{video_path.name}",
        )
# ================================