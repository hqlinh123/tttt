# app/utils/file_manager.py

import os
import shutil
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import asyncio
from fastapi import HTTPException
import librosa

from app.core.config.settings import WAVS_DIR

logger = logging.getLogger(__name__)


class FileManager:
    """Manager for audio file operations"""
    
    def __init__(self, audio_dir: str, max_age_hours: int = 24):
        """
        Initialize FileManager
        
        Args:
            audio_dir: Directory to store audio files
            max_age_hours: Maximum age of files in hours before cleanup
        """
        self.audio_dir = Path(audio_dir)
        self.max_age_hours = max_age_hours
        
        # Create directory if it doesn't exist
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"FileManager initialized with directory: {self.audio_dir}")
    
    # ---------------- FILE PATHS ----------------
    def get_audio_path(self, filename: str) -> Optional[Path]:
        """
        Get the full path to an audio file
        
        Args:
            filename: Name of the audio file
            
        Returns:
            Path object if file exists, None otherwise
        """
        try:
            # Sanitize filename to prevent path traversal
            safe_filename = self._sanitize_filename(filename)
            filepath = self.audio_dir / safe_filename
            
            if filepath.exists() and filepath.is_file():
                return filepath
            return None
        except Exception as e:
            logger.error(f"Error getting audio path for {filename}: {e}")
            return None
    
    def get_audio_url(self, filename: str, base_url: str = "/audio") -> str:
        """
        Generate URL for an audio file
        
        Args:
            filename: Name of the audio file
            base_url: Base URL prefix
            
        Returns:
            URL string
        """
        safe_filename = self._sanitize_filename(filename)
        return f"{base_url}/{safe_filename}"
    
    # ---------------- FILE OPERATIONS ----------------
    async def save_audio_file(
        self, 
        filename: str, 
        content: bytes,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Path:
        """
        Save audio file to disk
        
        Args:
            filename: Name of the file
            content: Binary content of the file
            metadata: Optional metadata to log
            
        Returns:
            Path to saved file
        """
        try:
            safe_filename = self._sanitize_filename(filename)
            filepath = self.audio_dir / safe_filename
            
            # Write file asynchronously
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._write_file, filepath, content)
            
            logger.info(f"Saved audio file: {filepath}")
            if metadata:
                logger.debug(f"File metadata: {metadata}")
            
            return filepath
        except Exception as e:
            logger.error(f"Failed to save audio file {filename}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to save audio file: {str(e)}")
    
    async def delete_audio(self, filename: str) -> bool:
        """
        Delete an audio file
        
        Args:
            filename: Name of the file to delete
            
        Returns:
            True if deleted, False if not found
        """
        try:
            safe_filename = self._sanitize_filename(filename)
            filepath = self.audio_dir / safe_filename
            
            if filepath.exists():
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self._delete_file, filepath)
                logger.info(f"Deleted audio file: {filepath}")
                return True
            else:
                logger.warning(f"Audio file not found for deletion: {filepath}")
                return False
        except Exception as e:
            logger.error(f"Failed to delete audio file {filename}: {e}")
            return False
    
    async def delete_audio_files(self, filenames: List[str]) -> Dict[str, bool]:
        """
        Delete multiple audio files
        
        Args:
            filenames: List of filenames to delete
            
        Returns:
            Dictionary mapping filename to success status
        """
        results = {}
        for filename in filenames:
            results[filename] = await self.delete_audio(filename)
        return results
    
    async def get_file_size(self, filename: str) -> Optional[int]:
        """
        Get file size in bytes
        
        Args:
            filename: Name of the file
            
        Returns:
            File size in bytes, None if file not found
        """
        filepath = self.get_audio_path(filename)
        if filepath:
            return filepath.stat().st_size
        return None
    
    async def get_file_info(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed file information
        
        Args:
            filename: Name of the file
            
        Returns:
            Dictionary with file information
        """
        filepath = self.get_audio_path(filename)
        if filepath:
            stat = filepath.stat()
            return {
                "filename": filename,
                "size_bytes": stat.st_size,
                "size_mb": stat.st_size / (1024 * 1024),
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "path": str(filepath)
            }
        return None
    
    # ---------------- CLEANUP ----------------
    async def cleanup_old_files(self) -> int:
        """
        Delete files older than max_age_hours
        
        Returns:
            Number of files deleted
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=self.max_age_hours)
            deleted_count = 0
            
            for filepath in self.audio_dir.iterdir():
                if filepath.is_file():
                    # Get file modification time
                    mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
                    
                    if mtime < cutoff_time:
                        loop = asyncio.get_event_loop()
                        await loop.run_in_executor(None, self._delete_file, filepath)
                        deleted_count += 1
                        logger.info(f"Cleaned up old file: {filepath}")
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old audio files")
            
            return deleted_count
        except Exception as e:
            logger.error(f"Failed to cleanup old files: {e}")
            return 0
    
    async def cleanup_by_size(self, max_size_mb: int = 1000) -> int:
        """
        Clean up files by size limit (delete oldest first)
        
        Args:
            max_size_mb: Maximum total size in MB
            
        Returns:
            Number of files deleted
        """
        try:
            # Get all files with their stats
            files = []
            total_size = 0
            
            for filepath in self.audio_dir.iterdir():
                if filepath.is_file():
                    size = filepath.stat().st_size
                    mtime = filepath.stat().st_mtime
                    files.append((filepath, size, mtime))
                    total_size += size
            
            total_size_mb = total_size / (1024 * 1024)
            
            if total_size_mb <= max_size_mb:
                return 0
            
            # Sort by modification time (oldest first)
            files.sort(key=lambda x: x[2])
            
            # Delete oldest until under limit
            deleted_count = 0
            for filepath, size, _ in files:
                if total_size_mb <= max_size_mb:
                    break
                
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self._delete_file, filepath)
                total_size_mb -= (size / (1024 * 1024))
                deleted_count += 1
                logger.info(f"Cleaned up file by size limit: {filepath}")
            
            logger.info(f"Cleaned up {deleted_count} files by size limit")
            return deleted_count
        except Exception as e:
            logger.error(f"Failed to cleanup by size: {e}")
            return 0
    
    # ---------------- STATISTICS ----------------
    def get_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics
        
        Returns:
            Dictionary with storage statistics
        """
        try:
            total_size = 0
            file_count = 0
            files_by_extension = {}
            
            for filepath in self.audio_dir.iterdir():
                if filepath.is_file():
                    file_count += 1
                    size = filepath.stat().st_size
                    total_size += size
                    
                    # Count by extension
                    ext = filepath.suffix.lower()
                    files_by_extension[ext] = files_by_extension.get(ext, 0) + 1
            
            return {
                "count": file_count,
                "total_size_bytes": total_size,
                "total_size_mb": total_size / (1024 * 1024),
                "total_size_gb": total_size / (1024 * 1024 * 1024),
                "files_by_extension": files_by_extension,
                "directory": str(self.audio_dir),
                "max_age_hours": self.max_age_hours
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {
                "count": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0,
                "total_size_gb": 0,
                "files_by_extension": {},
                "directory": str(self.audio_dir),
                "max_age_hours": self.max_age_hours
            }
    
    async def get_all_files(self) -> List[Dict[str, Any]]:
        """
        Get information for all files
        
        Returns:
            List of file information dictionaries
        """
        files = []
        for filepath in self.audio_dir.iterdir():
            if filepath.is_file():
                stat = filepath.stat()
                files.append({
                    "filename": filepath.name,
                    "size_bytes": stat.st_size,
                    "size_mb": stat.st_size / (1024 * 1024),
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "extension": filepath.suffix.lower()
                })
        
        # Sort by creation date (newest first)
        files.sort(key=lambda x: x["created_at"], reverse=True)
        return files
    
    # ---------------- UTILITIES ----------------
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to prevent path traversal attacks
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove any path separators
        filename = filename.replace('/', '_').replace('\\', '_')
        # Remove any directory traversal attempts
        filename = filename.replace('..', '_')
        # Remove any special characters
        import re
        filename = re.sub(r'[^\w\-_.]', '_', filename)
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:251] + ext
        return filename
    
    def _write_file(self, filepath: Path, content: bytes) -> None:
        """
        Write file to disk (synchronous)
        
        Args:
            filepath: Path to write to
            content: Binary content to write
        """
        with open(filepath, 'wb') as f:
            f.write(content)
    
    def _delete_file(self, filepath: Path) -> None:
        """
        Delete file from disk (synchronous)
        
        Args:
            filepath: Path to delete
        """
        if filepath.exists():
            filepath.unlink()
    
    async def ensure_directory_exists(self) -> None:
        """Ensure the audio directory exists"""
        self.audio_dir.mkdir(parents=True, exist_ok=True)
    
    async def get_disk_usage(self) -> Dict[str, Any]:
        """
        Get disk usage information
        
        Returns:
            Dictionary with disk usage stats
        """
        try:
            import shutil
            usage = shutil.disk_usage(self.audio_dir)
            return {
                "total_bytes": usage.total,
                "total_gb": usage.total / (1024 ** 3),
                "used_bytes": usage.used,
                "used_gb": usage.used / (1024 ** 3),
                "free_bytes": usage.free,
                "free_gb": usage.free / (1024 ** 3),
                "usage_percent": (usage.used / usage.total) * 100
            }
        except Exception as e:
            logger.error(f"Failed to get disk usage: {e}")
            return {}
    
    async def move_file(self, source_filename: str, dest_filename: str) -> bool:
        """
        Move/rename a file
        
        Args:
            source_filename: Current filename
            dest_filename: New filename
            
        Returns:
            True if successful, False otherwise
        """
        try:
            source_path = self.get_audio_path(source_filename)
            if not source_path:
                return False
            
            safe_dest = self._sanitize_filename(dest_filename)
            dest_path = self.audio_dir / safe_dest
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, shutil.move, source_path, dest_path)
            
            logger.info(f"Moved file: {source_filename} -> {dest_filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to move file: {e}")
            return False
    
    async def copy_file(self, source_filename: str, dest_filename: str) -> bool:
        """
        Copy a file
        
        Args:
            source_filename: Source filename
            dest_filename: Destination filename
            
        Returns:
            True if successful, False otherwise
        """
        try:
            source_path = self.get_audio_path(source_filename)
            if not source_path:
                return False
            
            safe_dest = self._sanitize_filename(dest_filename)
            dest_path = self.audio_dir / safe_dest
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, shutil.copy2, source_path, dest_path)
            
            logger.info(f"Copied file: {source_filename} -> {dest_filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to copy file: {e}")
            return False
   