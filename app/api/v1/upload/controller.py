# app/api/v1/upload/controller.py

from fastapi import Depends, UploadFile, File, HTTPException, status, BackgroundTasks
from typing import Optional
import logging
from datetime import datetime

from app.services.audio_upload_service import AudioUploadService
from app.core.deps import get_upload_service

logger = logging.getLogger(__name__)


# ---------------- UPLOAD SPEAKER AUDIO ----------------
async def upload_speaker_audio(
    file: UploadFile = File(..., description="Speaker audio file for voice cloning"),
    user_id: Optional[str] = None,
    upload_service: AudioUploadService = Depends(get_upload_service),
) -> dict:
    """
    Upload speaker audio file for voice cloning
    
    Requirements:
    - Format: WAV, MP3, M4A, FLAC
    - Max size: 10MB
    - Duration: 5-30 seconds recommended
    - Clear speech, no background noise
    """
    try:
        result = await upload_service.save_audio_file(file, user_id)
        
        return {
            "success": True,
            "message": "Audio file uploaded successfully",
            "speaker_id": result["speaker_id"],
            "file_path": result["file_path"],
            "file_url": result["file_url"],
            "duration": result["duration"],
            "filename": result["filename"],
            "file_size_mb": result["file_size"] / (1024 * 1024),
            "created_at": result["created_at"]
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error uploading speaker audio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}",
        )


# ---------------- GET SPEAKER AUDIO ----------------
async def get_speaker_audio(
    speaker_id: str,
    upload_service: AudioUploadService = Depends(get_upload_service),
) -> dict:
    """
    Get speaker audio file info by speaker ID
    """
    try:
        result = await upload_service.get_speaker_info(speaker_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Speaker audio not found",
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting speaker audio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get speaker info: {str(e)}",
        )


# ---------------- DOWNLOAD SPEAKER AUDIO ----------------
async def download_speaker_audio(
    speaker_id: str,
    upload_service: AudioUploadService = Depends(get_upload_service),
):
    """
    Download speaker audio file
    """
    from fastapi.responses import FileResponse
    
    try:
        file_path = await upload_service.get_speaker_file_path(speaker_id)
        
        if not file_path or not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Speaker audio not found",
            )
        
        return FileResponse(
            file_path,
            media_type="audio/wav",
            filename=file_path.name,
            headers={
                "Content-Disposition": f"attachment; filename={file_path.name}",
                "Content-Type": "audio/wav"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading speaker audio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Download failed: {str(e)}",
        )


# ---------------- DELETE SPEAKER AUDIO ----------------
async def delete_speaker_audio(
    speaker_id: str,
    upload_service: AudioUploadService = Depends(get_upload_service),
) -> dict:
    """
    Delete speaker audio file
    """
    try:
        success = await upload_service.delete_speaker_audio(speaker_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Speaker audio not found",
            )
        
        return {
            "success": True,
            "message": "Speaker audio deleted successfully",
            "speaker_id": speaker_id,
            "deleted_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting speaker audio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Delete failed: {str(e)}",
        )


# ---------------- LIST SPEAKER AUDIOS ----------------
async def list_speaker_audios(
    user_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    upload_service: AudioUploadService = Depends(get_upload_service),
) -> dict:
    """
    List all speaker audio files
    """
    try:
        result = await upload_service.list_speaker_audios(user_id, limit, offset)
        
        return {
            "success": True,
            "total": result["total"],
            "speakers": result["speakers"],
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error listing speaker audios: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list speakers: {str(e)}",
        )


# ---------------- UPDATE SPEAKER INFO ----------------
async def update_speaker_info(
    speaker_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[str] = None,
    upload_service: AudioUploadService = Depends(get_upload_service),
) -> dict:
    """
    Update speaker information (name, description, tags)
    """
    try:
        result = await upload_service.update_speaker_info(
            speaker_id, 
            name=name,
            description=description,
            tags=tags
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Speaker audio not found",
            )
        
        return {
            "success": True,
            "message": "Speaker info updated successfully",
            "speaker_id": speaker_id,
            "updated_at": datetime.now().isoformat(),
            "speaker": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating speaker info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Update failed: {str(e)}",
        )


# ---------------- GET SPEAKER STATS ----------------
async def get_speaker_stats(
    upload_service: AudioUploadService = Depends(get_upload_service),
) -> dict:
    """
    Get statistics about speaker audio files
    """
    try:
        stats = await upload_service.get_stats()
        
        return {
            "success": True,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting speaker stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}",
        )