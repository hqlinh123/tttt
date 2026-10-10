import uuid
import librosa
import soundfile as sf
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import HTTPException, BackgroundTasks
import logging

from app.infrastructure.repositories.voices_repository import VoicesRepository

logger = logging.getLogger(__name__)

class TTSService:
    def __init__(self, voices_repository: VoicesRepository, config: Optional[Dict[str, Any]] = None):
        self.voices_repository = voices_repository
        default_config = {
            "wavs_dir": "wavs",
            "output_dir": "outputs",
            "upload_dir": "uploads",
            "temp_dir": "temp",
            "model": None,
            "device": "cpu",
            "viterbox_available": False,
            "sample_rate": 22050,
            "language": "en",
        }
        if config is None:
            self.config = default_config
        else:
            self.config = {**default_config, **config}
        self.model = config.get("model")
        self.viterbox_available = config.get("viterbox_available", False)
        self.wavs_dir = Path(self.config["wavs_dir"])
        self.output_dir = Path(self.config["output_dir"])
        self.upload_dir = Path(self.config.get("upload_dir", "uploads"))
        self.temp_dir = Path(self.config.get("temp_dir", "temp"))
        
        # Ensure directories exist
        self.wavs_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    async def text_to_speech(self, request) -> dict:
        """Convert text to speech using default or selected voice"""
        if not self.viterbox_available:
            raise HTTPException(503, "Viterbox service not available. Please install Viterbox first.")
        
        try:
            # Get reference audio
            ref_audio = request.voice
            if not ref_audio or not Path(ref_audio).exists():
                # Try to find in wavs directory
                ref_audio = await self._get_random_voice()
            
            if not ref_audio:
                raise HTTPException(400, "No reference voice available. Please upload a voice sample first.")
            
            # Ensure the path is absolute or relative correctly
            ref_audio = await self._resolve_audio_path(ref_audio)
            
            # Generate speech
            audio_data = await self._generate_speech(
                text=request.text,
                language=request.language,
                ref_audio=ref_audio,
                exaggeration=request.exaggeration,
                cfg_weight=request.cfg_weight,
                temperature=request.temperature,
                sentence_pause_ms=request.sentence_pause_ms
            )
            
            # Save output
            output_path = await self._save_audio(audio_data)
            duration = len(audio_data) / self.model.sr if hasattr(self.model, 'sr') else 0
            
            return {
                "success": True,
                "message": "Generated successfully",
                "audio_url": f"/viterbox/outputs/{output_path.name}",
                "filename": output_path.name,
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
            logger.error(f"TTS generation failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def voice_clone(self, request) -> dict:
        """Clone voice from reference audio and synthesize text"""
        if not self.viterbox_available:
            raise HTTPException(503, "Viterbox service not available. Please install Viterbox first.")
        
        # Validate reference audio
        ref_path = await self._resolve_audio_path(request.reference_audio_path)
        
        try:
            logger.info(f"🎤 Generating with Viterbox...")
            logger.info(f"   Text: {request.text[:100]}...")
            logger.info(f"   Language: {request.language}")
            logger.info(f"   Reference: {ref_path}")
            
            # Generate speech with voice cloning
            audio_data = await self._generate_speech(
                text=request.text,
                language=request.language,
                ref_audio=str(ref_path),
                exaggeration=request.exaggeration,
                cfg_weight=request.cfg_weight,
                temperature=request.temperature,
                sentence_pause_ms=request.sentence_pause_ms
            )
            
            # Save output
            output_path = await self._save_audio(audio_data)
            duration = len(audio_data) / self.model.sr if hasattr(self.model, 'sr') else 0
            
            logger.info(f"✅ Generated! Duration: {duration:.2f}s")
            
            return {
                "success": True,
                "message": "Voice cloning completed successfully",
                "audio_url": f"/outputs/{output_path.name}",
                "filename": output_path.name,
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
            logger.error(f"Voice cloning failed: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Voice cloning failed: {str(e)}")
    
    async def tts_with_selected_voice(self, text: str, voice_file, language: str, 
                                       exaggeration: float, cfg_weight: float, 
                                       temperature: float, sentence_pause_ms: int) -> dict:
        """TTS with uploaded voice file (single request)"""
        if not self.viterbox_available:
            raise HTTPException(503, "Viterbox service not available")
        
        # Save uploaded voice file
        ext = Path(voice_file.filename).suffix.lower()
        if ext not in [".wav", ".mp3", ".m4a", ".flac"]:
            raise HTTPException(400, "Unsupported audio format")
        
        content = await voice_file.read()
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(400, "File too large. Max 10MB")
        
        temp_filename = f"temp_{uuid.uuid4().hex}{ext}"
        temp_path = self.temp_dir / temp_filename
        
        with open(temp_path, "wb") as f:
            f.write(content)
        
        try:
            # Generate speech
            audio_data = await self._generate_speech(
                text=text,
                language=language,
                ref_audio=str(temp_path),
                exaggeration=exaggeration,
                cfg_weight=cfg_weight,
                temperature=temperature,
                sentence_pause_ms=sentence_pause_ms
            )
            
            # Save output
            output_path = await self._save_audio(audio_data)
            duration = len(audio_data) / self.model.sr if hasattr(self.model, 'sr') else 0
            
            # Clean up temp file
            temp_path.unlink()
            
            return {
                "success": True,
                "audio_url": f"/outputs/{output_path.name}",
                "filename": output_path.name,
                "duration": round(duration, 2),
                "voice_cloning": True
            }
            
        except Exception as e:
            if temp_path.exists():
                temp_path.unlink()
            raise HTTPException(status_code=500, detail=str(e))
    
    async def upload_audio(self, file) -> dict:
        """Upload reference audio file for voice cloning"""
        if not self.viterbox_available:
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
        filepath = self.upload_dir / filename
        
        with open(filepath, "wb") as f:
            f.write(content)
        
        # Convert to WAV if not already
        if ext != ".wav":
            wav_filename = f"{uuid.uuid4().hex}.wav"
            wav_path = self.upload_dir / wav_filename
            
            try:
                # Load and convert to WAV
                y, sr = librosa.load(filepath, sr=16000, mono=True)
                sf.write(wav_path, y, sr)
                filepath = wav_path
                filename = wav_filename
                # Remove original file
                filepath.unlink()
            except Exception as e:
                raise HTTPException(400, f"Failed to convert audio: {str(e)}")
        
        duration = self.voice_service._get_audio_duration(filepath)
        
        return {
            "success": True,
            "speaker_id": filename.replace(".wav", ""),
            "filename": filename,
            "file_path": str(filepath),
            "duration": round(duration, 2),
            "message": "Upload successful. Use this file_path in /clone endpoint"
        }
    
    async def get_audio(self, filename: str) -> dict:
        """Get generated audio file"""
        file_path = self.output_dir / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        return {
            "file_path": file_path,
            "media_type": "audio/wav",
            "filename": filename
        }
    
    async def delete_audio(self, filename: str, background_tasks: BackgroundTasks):
        """Delete generated audio file"""
        file_path = self.output_dir / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        def remove_file():
            file_path.unlink()
        
        background_tasks.add_task(remove_file)
        
        return {
            "success": True,
            "message": f"Deleted {filename}"
        }
    
    async def delete_upload(self, filename: str) -> dict:
        """Delete uploaded reference audio file"""
        file_path = self.upload_dir / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        file_path.unlink()
        
        return {
            "success": True,
            "message": f"Deleted {filename}"
        }
    
    async def clear_outputs(self, background_tasks: BackgroundTasks) -> dict:
        """Clear all output files"""
        output_files = list(self.output_dir.glob("*.wav"))
        
        def clear_files():
            for file_path in output_files:
                try:
                    file_path.unlink()
                except Exception as e:
                    logger.error(f"Error deleting {file_path}: {e}")
        
        background_tasks.add_task(clear_files)
        
        return {
            "success": True,
            "message": f"Deleted {len(output_files)} output files",
            "deleted_count": len(output_files)
        }
    
    async def _generate_speech(self, text: str, language: str, ref_audio: str,
                               exaggeration: float, cfg_weight: float, 
                               temperature: float, sentence_pause_ms: int):
        """Generate speech using the model"""
        wav = self.model.generate(
            text=text,
            language=language,
            audio_prompt=ref_audio,
            exaggeration=exaggeration,
            cfg_weight=cfg_weight,
            temperature=temperature,
            sentence_pause_ms=sentence_pause_ms,
        )
        
        # Convert to numpy
        if hasattr(wav, 'cpu'):
            audio_np = wav[0].cpu().numpy()
        else:
            audio_np = wav[0] if isinstance(wav, (list, tuple)) else wav
        
        # Trim silence
        audio_np, _ = librosa.effects.trim(audio_np, top_db=30)
        
        return audio_np
    
    async def _save_audio(self, audio_data) -> Path:
        """Save audio data to file"""
        filename = f"{uuid.uuid4().hex}.wav"
        output_path = self.output_dir / filename
        sf.write(output_path, audio_data, self.model.sr if hasattr(self.model, 'sr') else 16000)
        return output_path
    
    async def _get_random_voice(self) -> Optional[str]:
        """Get a random voice file from wavs directory"""
        voice_files = list(self.wavs_dir.glob("*.wav"))
        if voice_files:
            import random
            return str(random.choice(voice_files))
        return None
    
    async def _resolve_audio_path(self, audio_path: str) -> Path:
        """Resolve audio file path"""
        ref_path = Path(audio_path)
        if not ref_path.exists():
            # Try to find in uploads directory
            alt_path = self.upload_dir / audio_path
            if alt_path.exists():
                ref_path = alt_path
            else:
                # Try in wavs directory
                wavs_path = self.wavs_dir / audio_path
                if wavs_path.exists():
                    ref_path = wavs_path
                else:
                    raise HTTPException(404, f"Reference audio not found: {audio_path}")
        return ref_path