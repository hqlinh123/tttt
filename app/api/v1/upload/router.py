# app/api/v1/upload/router.py

from fastapi import APIRouter

from app.api.v1.upload.controller import (
    upload_speaker_audio,
    get_speaker_audio,
    download_speaker_audio,
    delete_speaker_audio,
    list_speaker_audios,
    update_speaker_info,
    get_speaker_stats,
)

router = APIRouter()

# Upload endpoints
router.post("/speaker-audio")(upload_speaker_audio)

# Get endpoints
router.get("/speaker-audio/{speaker_id}")(get_speaker_audio)
router.get("/speaker-audio/{speaker_id}/download")(download_speaker_audio)
router.get("/speaker-audios")(list_speaker_audios)
router.get("/speaker-stats")(get_speaker_stats)

# Update endpoints
router.put("/speaker-audio/{speaker_id}")(update_speaker_info)

# Delete endpoints
router.delete("/speaker-audio/{speaker_id}")(delete_speaker_audio)