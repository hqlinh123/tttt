# app/api/v1/voices/router.py

from fastapi import APIRouter

from app.api.v1.voices.controller import (
    delete_audio,
    delete_upload,
    delete_voice,
    download_voice,
    get_audio,
    get_generated_voices,
    get_stats,
    get_voices,
    text_to_speech,
    upload_voice,
    voice_clone,
)
router = APIRouter()

# Voice management endpoints
router.get("/voices")(get_voices)
router.get("/voices/download/{filename}")(download_voice)
router.post("/tts")(text_to_speech)
router.post("/clone")(voice_clone)
router.post("/upload")(upload_voice)
router.delete("/voices/{filename}")(delete_voice)
router.get("/stats")(get_stats)
router.delete("/uploads/{filename}")(delete_upload)
router.delete("/outputs/{filename}")(delete_audio)
router.get("/outputs/{filename}")(get_audio)
router.get("/outputs")(get_generated_voices)
