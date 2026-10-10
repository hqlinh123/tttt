from fastapi import  Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from typing import Dict, Any
from app.core.deps import get_tts_service, get_voice_service
from app.domain.models.voices import TTSRequest, VoiceCloneRequest
import logging

from app.services.tts_service import TTSService
from app.services.voice_service import VoiceService

logger = logging.getLogger(__name__)

async def get_voices(voice_service: VoiceService = Depends(get_voice_service)) -> dict:
        try:
            return await voice_service.get_voices()
        except Exception as e:
            logger.error(f"Error getting voices: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )

async def download_voice( filename: str, voice_service: VoiceService = Depends(get_voice_service)):
        from fastapi.responses import FileResponse

        result = await voice_service.download_voice(filename)
        return FileResponse(
            path=result["file_path"],
            media_type=result["media_type"],
            filename=result["filename"],
            headers={
                "Content-Disposition": f"attachment; filename={result['filename']}",
                "Cache-Control": "public, max-age=86400"
            }
        )

async def upload_voice(
        voice_service: VoiceService = Depends(get_voice_service),
        file: UploadFile = File(...),
        background_tasks: BackgroundTasks = None
    ):
        result = await voice_service.upload_voice(file)

        if background_tasks:
            background_tasks.add_task(
                voice_service._convert_to_wav,
                result["file_path"]
            )

        return result

async def delete_voice(filename: str, voice_service: VoiceService = Depends(get_voice_service)):

        return await voice_service.delete_voice(filename)

async def get_stats(voice_service: VoiceService = Depends(get_voice_service)) -> Dict[str, Any]:
        return await voice_service.get_stats()

async def upload_audio(tts: TTSService = Depends(get_tts_service), file: UploadFile = File(...)):
        return await tts.upload_audio(file)

async def text_to_speech( request: TTSRequest, tts: TTSService = Depends(get_tts_service)):
        return await tts.text_to_speech(request)

async def voice_clone(request: VoiceCloneRequest, tts: TTSService = Depends(get_tts_service)):
        return await tts.voice_clone(request)

async def tts_with_selected_voice(
        
        text: str,
        voice_file: UploadFile = File(...),
        language: str = "vi",
        exaggeration: float = 0.5,
        cfg_weight: float = 0.5,
        temperature: float = 0.8,
        sentence_pause_ms: int = 500,
        tts: TTSService = Depends(get_tts_service),
    ):
        return await tts.tts_with_selected_voice(
            text,
            voice_file,
            language,
            exaggeration,
            cfg_weight,
            temperature,
            sentence_pause_ms
        )

async def get_audio(filename: str, tts: TTSService = Depends(get_tts_service)):
        from fastapi.responses import FileResponse

        result = await tts.get_audio(filename)
        return FileResponse(
            path=result["file_path"],
            media_type=result["media_type"],
            filename=result["filename"],
            headers={
                "Content-Disposition": f"inline; filename={result['filename']}",
                "Cache-Control": "public, max-age=3600"
            }
        )

async def delete_audio(filename: str, background_tasks: BackgroundTasks,tts: TTSService = Depends(get_tts_service)):
        return await tts.delete_audio(filename, background_tasks)

async def delete_upload(filename: str,tts: TTSService = Depends(get_tts_service)):
        return await tts.delete_upload(filename)

async def clear_outputs(background_tasks: BackgroundTasks, tts: TTSService = Depends(get_tts_service)):
        return await tts.clear_outputs(background_tasks)

async def get_generated_voices(voice_service: VoiceService = Depends(get_voice_service)):
    return await voice_service.get_generated_voices()