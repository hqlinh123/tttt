"""
Viterbox FastAPI Server
Run:
    uvicorn app:app --host 0.0.0.0 --port 8000 --reload

Docs:
    http://localhost:8000/docs
"""

import os
import uuid
import random
import warnings
import tempfile
import shutil
from datetime import datetime

from pathlib import Path
from typing import Optional

import torch
import librosa
import soundfile as sf
import numpy as np

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from uvicorn import lifespan

from app.core.config import settings

# Try to import Viterbox with error handling
try:
    from viterbox import Viterbox
    VITERBOX_AVAILABLE = True
except ImportError as e:
    VITERBOX_AVAILABLE = False
    print(f"⚠️ Viterbox not available: {e}")
    print("Please install: git clone https://github.com/iamdinhthuan/viterbox-tts.git && cd viterbox-tts && pip install -e .")

warnings.filterwarnings("ignore")

# =========================================================
# CONFIG
# =========================================================

os.environ["GRADIO_TEMP_DIR"] = tempfile.gettempdir() + "/my_gradio_tmp"
os.makedirs(os.environ["GRADIO_TEMP_DIR"], exist_ok=True)

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

WAVS_DIR = Path("wavs")
WAVS_DIR.mkdir(exist_ok=True)

# =========================================================
# FASTAPI
# =========================================================

app = FastAPI(
    title="Viterbox TTS API",
    description="Text-to-Speech and Voice Cloning API using Viterbox",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://192.168.0.46:8000",
        "https://frenzy-wrinkly-stellar.ngrok-free.dev",
        "https://*.ngrok-free.dev",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Content-Type",
        "Accept",
        "Authorization",
        "ngrok-skip-browser-warning",
        "X-Requested-With",
        "Access-Control-Allow-Origin"
    ],
    expose_headers=["Content-Type", "Content-Length"],
    max_age=3600,
)

# Mount static directories
app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR)), name="outputs")
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
app.mount("/wavs", StaticFiles(directory=str(WAVS_DIR)), name="wavs")

# =========================================================
# LOAD MODEL
# =========================================================

print("=" * 50)
print("🚀 Loading Viterbox...")
print("=" * 50)

if VITERBOX_AVAILABLE:
    if torch.cuda.is_available():
        DEVICE = "cuda"
    elif torch.backends.mps.is_available():
        DEVICE = "mps"
    else:
        DEVICE = "cpu"

    print(f"Device: {DEVICE}")

    try:
        MODEL = Viterbox.from_pretrained(DEVICE)
        print("✅ Model loaded!")
    except Exception as e:
        MODEL = None
        VITERBOX_AVAILABLE = False
        print(f"⚠️ Failed to load model: {e}")
else:
    MODEL = None
    print("⚠️ Viterbox not installed. Voice cloning will not work.")

print("=" * 50)

# =========================================================
# HELPERS
# =========================================================

def list_voices():
    """List available voice files in wavs directory"""
    if WAVS_DIR.exists():
        return sorted([str(f) for f in WAVS_DIR.glob("*.wav")])
    return []

def get_random_voice():
    voices = list_voices()
    if voices:
        return random.choice(voices)
    return None

def get_audio_duration(filepath: Path) -> float:
    """Get audio duration in seconds"""
    try:
        y, sr = librosa.load(filepath, sr=None)
        return len(y) / sr
    except Exception:
        return 0.0

def get_voice_display_name(filename: str) -> str:
    """Convert filename to display name"""
    name = filename.replace('.wav', '').replace('.mp3', '')
    voice_names = {
        'hien': 'Hiền',
        'ngoc': 'Ngọc',
        'linh': 'Linh',
        'trang': 'Trang',
        'mai': 'Mai',
        'huong': 'Hương',
        'thao': 'Thảo',
        'van': 'Vân',
        'anh': 'Anh',
        'lan': 'Lan',
        'ha': 'Hà',
        'hoa': 'Hoa',
        'thanh': 'Thanh',
        'phuong': 'Phương',
        'thuy': 'Thủy',
    }
    return voice_names.get(name.lower(), name.capitalize())

# =========================================================
# REQUEST MODELS
# =========================================================

class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    language: str = Field("vi", description="Language: vi, en, es, fr, de, zh, ja, ko")
    exaggeration: float = Field(0.5, ge=0.0, le=2.0)
    cfg_weight: float = Field(0.5, ge=0.0, le=1.0)
    temperature: float = Field(0.8, ge=0.1, le=1.0)
    sentence_pause_ms: int = Field(500, ge=0, le=2000, description="Pause between sentences (milliseconds)")
    voice: Optional[str] = Field(None, description="Voice file to use (optional)")

class VoiceCloneRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    reference_audio_path: str = Field(..., description="Path to reference audio file")
    language: str = Field("vi")
    exaggeration: float = Field(0.5, ge=0.0, le=2.0)
    cfg_weight: float = Field(0.5, ge=0.0, le=1.0)
    temperature: float = Field(0.8, ge=0.1, le=1.0)
    sentence_pause_ms: int = Field(500, ge=0, le=2000)

# =========================================================
# ROUTES
# =========================================================

@app.get("/")
async def root():
    return {
        "message": "Viterbox TTS API",
        "version": "1.0.0",
        "viterbox_available": VITERBOX_AVAILABLE,
        "docs": "/docs",
        "endpoints": {
            "POST /v1/viterbox/tts": "Text to speech with default voice",
            "POST /v1/viterbox/clone": "Voice cloning with reference audio",
            "POST /v1/viterbox/upload": "Upload reference audio",
            "GET /v1/viterbox/voices": "List available voices",
            "GET /v1/viterbox/voices/download/{filename}": "Download a specific voice file",
            "POST /v1/viterbox/voices/upload": "Upload a new voice file to wavs directory",
            "DELETE /v1/viterbox/voices/{filename}": "Delete a voice file",
            "GET /v1/viterbox/stats": "Service statistics",
            "GET /outputs/{filename}": "Download generated audio"
        }
    }

@app.get("/v1/viterbox/voices")
async def get_voices():
    """Get available voices from wavs directory with display names and metadata"""
    voices = list_voices()
    voice_list = []
    
    for voice_path in voices:
        voice_path_obj = Path(voice_path)
        filename = voice_path_obj.name
        display_name = get_voice_display_name(filename)
        duration = get_audio_duration(voice_path_obj)
        
        voice_list.append({
            "id": filename,
            "name": display_name,
            "filename": filename,
            "duration": round(duration, 2),
            "url": f"/wavs/{filename}",
            "download_url": f"/v1/viterbox/voices/download/{filename}"
        })
    
    return {
        "success": True,
        "count": len(voice_list),
        "voices": voice_list,
        "viterbox_available": VITERBOX_AVAILABLE
    }

@app.get("/v1/viterbox/voices/download/{filename}")
async def download_voice(filename: str):
    """
    Download a specific voice file from the wavs directory
    """
    # Security: Prevent path traversal attacks
    if ".." in filename or filename.startswith("/"):
        raise HTTPException(400, "Invalid filename")
    
    # Check in wavs directory
    file_path = WAVS_DIR / filename
    
    # Also check in uploads directory as fallback
    if not file_path.exists():
        file_path = UPLOAD_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(404, f"Voice file '{filename}' not found")
    
    # Get file extension for correct media type
    ext = file_path.suffix.lower()
    media_type = "audio/wav" if ext == ".wav" else "audio/mpeg"
    
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename,
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Cache-Control": "public, max-age=86400"  # Cache for 24 hours
        }
    )

@app.post("/v1/viterbox/voices/upload")
async def upload_voice(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Upload a new voice file to the wavs directory for voice selection
    Supports: .wav, .mp3, .m4a, .flac (max 10MB)
    """
    # Validate extension
    allowed_extensions = [".wav", ".mp3", ".m4a", ".flac"]
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed_extensions:
        raise HTTPException(400, f"Unsupported format. Allowed: {allowed_extensions}")
    
    # Validate size
    content = await file.read()
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(400, "File too large. Max 10MB")
    
    # Generate a clean filename
    original_name = Path(file.filename).stem
    # Replace spaces and special characters
    clean_name = "".join(c for c in original_name if c.isalnum() or c in "._- ").strip()
    clean_name = clean_name.lower().replace(" ", "_")
    
    # Ensure unique filename
    target_filename = f"{clean_name}{ext}"
    target_path = WAVS_DIR / target_filename
    
    # If file exists, add a number suffix
    counter = 1
    while target_path.exists():
        target_filename = f"{clean_name}_{counter}{ext}"
        target_path = WAVS_DIR / target_filename
        counter += 1
    
    # Save the uploaded file
    with open(target_path, "wb") as f:
        f.write(content)
    
    # Convert to WAV if not already (in background)
    def convert_to_wav():
        if ext != ".wav":
            try:
                wav_filename = target_path.stem + ".wav"
                wav_path = WAVS_DIR / wav_filename
                y, sr = librosa.load(target_path, sr=16000, mono=True)
                sf.write(wav_path, y, sr)
                # Remove original non-wav file
                target_path.unlink()
                return wav_path
            except Exception as e:
                print(f"Conversion error: {e}")
        return target_path
    
    # Run conversion in background
    background_tasks.add_task(convert_to_wav)
    
    duration = get_audio_duration(target_path)
    display_name = get_voice_display_name(target_filename)
    
    return {
        "success": True,
        "message": "Voice file uploaded successfully",
        "voice": {
            "id": target_filename,
            "name": display_name,
            "filename": target_filename,
            "duration": round(duration, 2),
            "url": f"/wavs/{target_filename}",
            "download_url": f"/v1/viterbox/voices/download/{target_filename}"
        }
    }

@app.delete("/v1/viterbox/voices/{filename}")
async def delete_voice(filename: str):
    """
    Delete a voice file from the wavs directory
    """
    # Security: Prevent path traversal attacks
    if ".." in filename or filename.startswith("/"):
        raise HTTPException(400, "Invalid filename")
    
    file_path = WAVS_DIR / filename
    
    if not file_path.exists():
        # Also check in uploads directory
        file_path = UPLOAD_DIR / filename
        if not file_path.exists():
            raise HTTPException(404, f"Voice file '{filename}' not found")
    
    # Delete the file
    file_path.unlink()
    
    # Also delete any associated converted files
    if file_path.suffix != ".wav":
        wav_path = file_path.with_suffix(".wav")
        if wav_path.exists():
            wav_path.unlink()
    
    return {
        "success": True,
        "message": f"Deleted voice file '{filename}'"
    }

@app.get("/v1/viterbox/stats")
async def get_stats():
    """Get service statistics"""
    output_files = list(OUTPUT_DIR.glob("*.wav"))
    upload_files = list(UPLOAD_DIR.glob("*"))
    voice_files = list_voices()
    
    total_size = sum(f.stat().st_size for f in output_files)
    voices_size = sum(f.stat().st_size for f in voice_files) if voice_files else 0
    
    return {
        "success": True,
        "viterbox_available": VITERBOX_AVAILABLE,
        "device": DEVICE if VITERBOX_AVAILABLE else None,
        "total_audio_files": len(output_files),
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "uploaded_files": len(upload_files),
        "available_voices": len(voice_files),
        "voices_size_mb": round(voices_size / (1024 * 1024), 2)
    }

@app.post("/v1/viterbox/upload")
async def upload_audio(file: UploadFile = File(...)):
    """
    Upload reference audio file for voice cloning
    Supports: .wav, .mp3, .m4a, .flac (max 10MB)
    """
    if not VITERBOX_AVAILABLE:
        raise HTTPException(503, "Viterbox service not available")
    
    # Validate extension
    allowed_extensions = [".wav", ".mp3", ".m4a", ".flac"]
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed_extensions:
        raise HTTPException(400, f"Unsupported format. Allowed: {allowed_extensions}")
    
    # Validate size
    content = await file.read()
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(400, "File too large. Max 10MB")
    
    # Save file
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = UPLOAD_DIR / filename
    
    with open(filepath, "wb") as f:
        f.write(content)
    
    # Convert to WAV if not already
    if ext != ".wav":
        wav_filename = f"{uuid.uuid4().hex}.wav"
        wav_path = UPLOAD_DIR / wav_filename
        
        try:
            # Load and convert to WAV
            y, sr = librosa.load(filepath, sr=16000, mono=True)
            sf.write(wav_path, y, sr)
            filepath = wav_path
            filename = wav_filename
            # Remove original file
            Path(filepath).unlink()
        except Exception as e:
            raise HTTPException(400, f"Failed to convert audio: {str(e)}")
    
    duration = get_audio_duration(filepath)
    
    return {
        "success": True,
        "speaker_id": filename.replace(".wav", ""),
        "filename": filename,
        "file_path": str(filepath),
        "duration": round(duration, 2),
        "message": "Upload successful. Use this file_path in /clone endpoint"
    }

@app.post("/v1/viterbox/tts")
async def text_to_speech(request: TTSRequest):
    """Convert text to speech using default or selected voice"""
    if not VITERBOX_AVAILABLE:
        raise HTTPException(503, "Viterbox service not available. Please install Viterbox first.")
    
    try:
        # Get reference audio
        ref_audio = request.voice
        if not ref_audio or not Path(ref_audio).exists():
            # Try to find in wavs directory
            ref_audio = get_random_voice()
        
        if not ref_audio:
            raise HTTPException(400, "No reference voice available. Please upload a voice sample first.")
        
        # Ensure the path is absolute or relative correctly
        if not Path(ref_audio).is_absolute():
            # Check if file exists in wavs directory
            wavs_path = WAVS_DIR / ref_audio
            if wavs_path.exists():
                ref_audio = str(wavs_path)
            else:
                # Check in uploads directory
                uploads_path = UPLOAD_DIR / ref_audio
                if uploads_path.exists():
                    ref_audio = str(uploads_path)
        
        # Generate speech
        wav = MODEL.generate(
            text=request.text,
            language=request.language,
            audio_prompt=ref_audio,
            exaggeration=request.exaggeration,
            cfg_weight=request.cfg_weight,
            temperature=request.temperature,
            sentence_pause_ms=request.sentence_pause_ms,
        )
        
        # Convert to numpy
        audio_np = wav[0].cpu().numpy()
        
        # Trim silence
        audio_np, _ = librosa.effects.trim(audio_np, top_db=30)
        
        # Save output
        filename = f"{uuid.uuid4().hex}.wav"
        output_path = OUTPUT_DIR / filename
        sf.write(output_path, audio_np, MODEL.sr)
        
        duration = len(audio_np) / MODEL.sr
        
        return {
            "success": True,
            "message": "Generated successfully",
            "audio_url": f"/outputs/{filename}",
            "filename": filename,
            "duration": round(duration, 2),
            "text_length": len(request.text),
            "language": request.language,
            "voice_cloning": False,
            "voice_used": Path(ref_audio).name if ref_audio else None,
            "params": {
                "exaggeration": request.exaggeration,
                "cfg_weight": request.cfg_weight,
                "temperature": request.temperature,
                "sentence_pause_ms": request.sentence_pause_ms
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/viterbox/clone")
async def voice_clone(request: VoiceCloneRequest):
    """
    Clone voice from reference audio and synthesize text
    This is the main endpoint for voice cloning
    """
    if not VITERBOX_AVAILABLE:
        raise HTTPException(503, "Viterbox service not available. Please install Viterbox first.")
    
    # Validate reference audio
    ref_path = Path(request.reference_audio_path)
    if not ref_path.exists():
        # Try to find in uploads directory
        alt_path = UPLOAD_DIR / request.reference_audio_path
        if alt_path.exists():
            ref_path = alt_path
        else:
            # Try in wavs directory
            wavs_path = WAVS_DIR / request.reference_audio_path
            if wavs_path.exists():
                ref_path = wavs_path
            else:
                raise HTTPException(404, f"Reference audio not found: {request.reference_audio_path}")
    
    try:
        print(f"🎤 Generating with Viterbox...")
        print(f"   Text: {request.text[:100]}...")
        print(f"   Language: {request.language}")
        print(f"   Reference: {ref_path}")
        print(f"   Params: exh={request.exaggeration}, cfg={request.cfg_weight}, temp={request.temperature}, pause={request.sentence_pause_ms}ms")
        
        # Generate speech with voice cloning
        wav = MODEL.generate(
            text=request.text,
            language=request.language,
            audio_prompt=str(ref_path),
            exaggeration=request.exaggeration,
            cfg_weight=request.cfg_weight,
            temperature=request.temperature,
            sentence_pause_ms=request.sentence_pause_ms,
        )
        
        # Convert to numpy
        if hasattr(wav, 'cpu'):
            audio_np = wav[0].cpu().numpy()
        else:
            audio_np = wav[0] if isinstance(wav, (list, tuple)) else wav
        
        # Trim silence
        audio_np, _ = librosa.effects.trim(audio_np, top_db=30)
        
        # Save output
        filename = f"{uuid.uuid4().hex}.wav"
        output_path = OUTPUT_DIR / filename
        sf.write(output_path, audio_np, MODEL.sr)
        
        duration = len(audio_np) / MODEL.sr
        
        print(f"✅ Generated! Duration: {duration:.2f}s")
        
        return {
            "success": True,
            "message": "Voice cloning completed successfully",
            "audio_url": f"/outputs/{filename}",
            "filename": filename,
            "duration": round(duration, 2),
            "text_length": len(request.text),
            "language": request.language,
            "voice_cloning": True,
            "reference_voice": ref_path.name,
            "params": {
                "exaggeration": request.exaggeration,
                "cfg_weight": request.cfg_weight,
                "temperature": request.temperature,
                "sentence_pause_ms": request.sentence_pause_ms
            }
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Voice cloning failed: {str(e)}")

@app.post("/v1/viterbox/tts-with-voice")
async def tts_with_selected_voice(
    text: str = Form(...),
    voice_file: UploadFile = File(...),
    language: str = Form("vi"),
    exaggeration: float = Form(0.5),
    cfg_weight: float = Form(0.5),
    temperature: float = Form(0.8),
    sentence_pause_ms: int = Form(500)
):
    """TTS with uploaded voice file (single request)"""
    if not VITERBOX_AVAILABLE:
        raise HTTPException(503, "Viterbox service not available")
    
    # Save uploaded voice file
    ext = Path(voice_file.filename).suffix.lower()
    if ext not in [".wav", ".mp3", ".m4a", ".flac"]:
        raise HTTPException(400, "Unsupported audio format")
    
    content = await voice_file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(400, "File too large. Max 10MB")
    
    temp_filename = f"temp_{uuid.uuid4().hex}{ext}"
    temp_path = TEMP_DIR / temp_filename
    
    with open(temp_path, "wb") as f:
        f.write(content)
    
    try:
        # Generate speech
        wav = MODEL.generate(
            text=text,
            language=language,
            audio_prompt=str(temp_path),
            exaggeration=exaggeration,
            cfg_weight=cfg_weight,
            temperature=temperature,
            sentence_pause_ms=sentence_pause_ms,
        )
        
        audio_np = wav[0].cpu().numpy()
        audio_np, _ = librosa.effects.trim(audio_np, top_db=30)
        
        filename = f"{uuid.uuid4().hex}.wav"
        output_path = OUTPUT_DIR / filename
        sf.write(output_path, audio_np, MODEL.sr)
        
        duration = len(audio_np) / MODEL.sr
        
        # Clean up temp file
        temp_path.unlink()
        
        return {
            "success": True,
            "audio_url": f"/outputs/{filename}",
            "filename": filename,
            "duration": round(duration, 2),
            "voice_cloning": True
        }
        
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/outputs/{filename}")
async def get_audio(filename: str):
    """Download generated audio file"""
    file_path = OUTPUT_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    return FileResponse(
        path=file_path,
        media_type="audio/wav",
        filename=filename,
        headers={
            "Content-Disposition": f"inline; filename={filename}",
            "Cache-Control": "public, max-age=3600"
        }
    )

@app.delete("/outputs/{filename}")
async def delete_audio(filename: str, background_tasks: BackgroundTasks):
    """Delete generated audio file"""
    file_path = OUTPUT_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    def remove_file():
        file_path.unlink()
    
    background_tasks.add_task(remove_file)
    
    return {
        "success": True,
        "message": f"Deleted {filename}"
    }

@app.delete("/v1/viterbox/uploads/{filename}")
async def delete_upload(filename: str):
    """Delete uploaded reference audio file"""
    file_path = UPLOAD_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    file_path.unlink()
    
    return {
        "success": True,
        "message": f"Deleted {filename}"
    }

@app.post("/v1/viterbox/clear-outputs")
async def clear_outputs(background_tasks: BackgroundTasks):
    """Clear all generated audio files"""
    output_files = list(OUTPUT_DIR.glob("*.wav"))
    
    def remove_all():
        for f in output_files:
            f.unlink()
    
    background_tasks.add_task(remove_all)
    
    return {
        "success": True,
        "message": f"Deleting {len(output_files)} files"
    }

# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "viterbox_available": VITERBOX_AVAILABLE,
        "device": DEVICE if VITERBOX_AVAILABLE else None,
        "timestamp": datetime.now().isoformat()
    }

# =========================================================
# MAIN
# =========================================================

def create_app() -> FastAPI:
    """
    Application Factory
    - Production ready
    - Test friendly
    - Worker friendly
    """
    
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="AI Video REST API",
        lifespan=lifespan,
        docs_url="/docs" if settings.ENABLE_DOCS else None,
        redoc_url="/redoc" if settings.ENABLE_DOCS else None,
        openapi_url="/openapi.json" if settings.ENABLE_DOCS else None,
    )
    
    # ---------------- CORS ----------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # ---------------- Routers ----------------
    app.include_router(
        api_router,
        prefix=settings.API_PREFIX,
    )
    
    # ---------------- Root Endpoint ----------------
    @app.get("/")
    async def root():
        return {
            "message": "AI Video Backend API",
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "status": "running"
        }
    
    # ---------------- Health Check ----------------
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "timestamp": __import__('datetime').datetime.now().isoformat(),
            "version": settings.APP_VERSION
        }
    
    return app

app = create_app()
if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "=" * 50)
    print("🚀 Starting Viterbox TTS Server")
    print("=" * 50)
    print(f"Output directory: {OUTPUT_DIR.absolute()}")
    print(f"Upload directory: {UPLOAD_DIR.absolute()}")
    print(f"Wavs directory: {WAVS_DIR.absolute()}")
    print(f"Viterbox available: {VITERBOX_AVAILABLE}")
    print("=" * 50 + "\n")
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )