from asyncio import subprocess

from fastapi import Path, logger


def _get_video_duration(
    self,
    video_path: Path,
) -> float:
    try:
        command = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(video_path),
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
        )

        return float(
            result.stdout.strip()
        )

    except Exception as exc:
        logger.warning(
            "Cannot read video duration %s: %s",
            video_path,
            exc,
        )

        return 0.0