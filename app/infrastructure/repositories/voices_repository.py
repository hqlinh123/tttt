from pathlib import Path
import librosa
import soundfile as sf

from app.core.config.settings import UPLOAD_DIR, WAVS_DIR
from sqlalchemy.ext.asyncio import AsyncSession

class VoicesRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    def list_voices(self):
        return sorted([f for f in WAVS_DIR.glob("*.wav")])

    def get_voice(self, filename: str) -> Path | None:
        path = WAVS_DIR / filename
        if path.exists():
            return path

        path = UPLOAD_DIR / filename
        if path.exists():
            return path

        return None

    def save_voice(self, filename: str, content: bytes) -> Path:
        path = WAVS_DIR / filename
        with open(path, "wb") as f:
            f.write(content)
        return path

    def delete_voice(self, filename: str):
        path = self.get_voice(filename)
        if path:
            path.unlink()

    def convert_to_wav(self, path: Path) -> Path:
        if path.suffix == ".wav":
            return path

        wav_path = path.with_suffix(".wav")

        y, sr = librosa.load(path, sr=16000, mono=True)
        sf.write(wav_path, y, sr)

        path.unlink()
        return wav_path