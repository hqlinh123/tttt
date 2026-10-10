# app/infrastructure/repositories/audio_record_repository.py

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func
from datetime import datetime, timedelta
import logging

from app.domain.models.audio_record import AudioRecord

logger = logging.getLogger(__name__)


class AudioRecordRepository:
    """Repository for audio record database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ---------------- CREATE ----------------
    async def create(self, data: Dict[str, Any]) -> AudioRecord:
        """Create a new audio record"""
        try:
            record = AudioRecord(**data)
            self.db.add(record)
            await self.db.commit()
            await self.db.refresh(record)
            logger.info(f"Created audio record: id={record.id}, filename={record.filename}")
            return record
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create audio record: {e}")
            raise
    
    async def bulk_create(self, records_data: List[Dict[str, Any]]) -> List[AudioRecord]:
        """Create multiple audio records in bulk"""
        try:
            records = []
            for data in records_data:
                record = AudioRecord(**data)
                records.append(record)
            
            self.db.add_all(records)
            await self.db.commit()
            
            for record in records:
                await self.db.refresh(record)
            
            logger.info(f"Bulk created {len(records)} audio records")
            return records
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to bulk create audio records: {e}")
            raise
    
    # ---------------- READ ----------------
    async def get_by_id(self, record_id: int) -> Optional[AudioRecord]:
        """Get record by ID"""
        try:
            return self.db.query(AudioRecord).filter(AudioRecord.id == record_id).first()
        except Exception as e:
            logger.error(f"Failed to get record by id {record_id}: {e}")
            return None
    
    async def get_by_filename(self, filename: str) -> Optional[AudioRecord]:
        """Get record by filename"""
        try:
            return self.db.query(AudioRecord).filter(AudioRecord.filename == filename).first()
        except Exception as e:
            logger.error(f"Failed to get record by filename {filename}: {e}")
            return None
    
    async def get_by_user(
        self, 
        user_id: str, 
        limit: int = 50, 
        offset: int = 0,
        status: Optional[str] = None
    ) -> List[AudioRecord]:
        """Get records by user ID"""
        try:
            query = self.db.query(AudioRecord).filter(AudioRecord.user_id == user_id)
            
            if status:
                query = query.filter(AudioRecord.status == status)
            
            records = query.order_by(desc(AudioRecord.created_at))\
                .limit(limit)\
                .offset(offset)\
                .all()
            
            return records
        except Exception as e:
            logger.error(f"Failed to get records by user {user_id}: {e}")
            return []
    
    async def get_by_voice(
        self, 
        voice_id: str, 
        limit: int = 100,
        offset: int = 0
    ) -> List[AudioRecord]:
        """Get records by voice ID"""
        try:
            records = self.db.query(AudioRecord)\
                .filter(AudioRecord.voice_id == voice_id)\
                .order_by(desc(AudioRecord.created_at))\
                .limit(limit)\
                .offset(offset)\
                .all()
            
            return records
        except Exception as e:
            logger.error(f"Failed to get records by voice {voice_id}: {e}")
            return []
    
    async def get_recent_records(
        self, 
        hours: int = 24, 
        limit: int = 100
    ) -> List[AudioRecord]:
        """Get recent records within specified hours"""
        try:
            since_time = datetime.now() - timedelta(hours=hours)
            records = self.db.query(AudioRecord)\
                .filter(AudioRecord.created_at >= since_time)\
                .order_by(desc(AudioRecord.created_at))\
                .limit(limit)\
                .all()
            
            return records
        except Exception as e:
            logger.error(f"Failed to get recent records: {e}")
            return []
    
    async def get_by_status(
        self, 
        status: str, 
        limit: int = 100
    ) -> List[AudioRecord]:
        """Get records by status"""
        try:
            records = self.db.query(AudioRecord)\
                .filter(AudioRecord.status == status)\
                .order_by(AudioRecord.created_at)\
                .limit(limit)\
                .all()
            
            return records
        except Exception as e:
            logger.error(f"Failed to get records by status {status}: {e}")
            return []
    
    async def get_voice_cloning_records(
        self, 
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> List[AudioRecord]:
        """Get voice cloning records"""
        try:
            query = self.db.query(AudioRecord).filter(AudioRecord.is_voice_cloning == True)
            
            if user_id:
                query = query.filter(AudioRecord.user_id == user_id)
            
            records = query.order_by(desc(AudioRecord.created_at))\
                .limit(limit)\
                .all()
            
            return records
        except Exception as e:
            logger.error(f"Failed to get voice cloning records: {e}")
            return []
    
    async def count_user_records(self, user_id: str) -> int:
        """Count total records for a user"""
        try:
            count = self.db.query(AudioRecord).filter(AudioRecord.user_id == user_id).count()
            return count
        except Exception as e:
            logger.error(f"Failed to count records for user {user_id}: {e}")
            return 0
    
    # ---------------- UPDATE ----------------
    async def update(self, record_id: int, update_data: Dict[str, Any]) -> Optional[AudioRecord]:
        """Update an audio record"""
        try:
            record = await self.get_by_id(record_id)
            if not record:
                logger.warning(f"Record {record_id} not found for update")
                return None
            
            for key, value in update_data.items():
                if hasattr(record, key) and value is not None:
                    setattr(record, key, value)
            
            await self.db.commit()
            await self.db.refresh(record)
            
            logger.info(f"Updated record {record_id}")
            return record
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update record {record_id}: {e}")
            return None
    
    async def update_status(
        self, 
        record_id: int, 
        status: str, 
        error_message: Optional[str] = None
    ) -> Optional[AudioRecord]:
        """Update record status"""
        return await self.update(
            record_id, 
            {
                "status": status,
                "error_message": error_message
            }
        )
    
    async def increment_retry_count(self, record_id: int) -> Optional[AudioRecord]:
        """Increment retry count for failed record"""
        try:
            record = await self.get_by_id(record_id)
            if record:
                record.retry_count = (record.retry_count or 0) + 1
                await self.db.commit()
                await self.db.refresh(record)
            return record
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to increment retry count for record {record_id}: {e}")
            return None
    
    # ---------------- DELETE ----------------
    async def delete(self, record_id: int) -> bool:
        """Delete record by ID"""
        try:
            record = await self.get_by_id(record_id)
            if record:
                self.db.delete(record)
                await self.db.commit()
                logger.info(f"Deleted record {record_id}")
                return True
            return False
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete record {record_id}: {e}")
            return False
    
    async def delete_by_user(self, user_id: str) -> int:
        """Delete all records for a user"""
        try:
            deleted_count = self.db.query(AudioRecord)\
                .filter(AudioRecord.user_id == user_id)\
                .delete()
            await self.db.commit()
            
            logger.info(f"Deleted {deleted_count} records for user {user_id}")
            return deleted_count
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete records for user {user_id}: {e}")
            return 0
    
    async def delete_old_records(self, days: int = 30) -> int:
        """Delete records older than specified days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            deleted_count = self.db.query(AudioRecord)\
                .filter(AudioRecord.created_at < cutoff_date)\
                .delete()
            await self.db.commit()
            
            logger.info(f"Deleted {deleted_count} records older than {days} days")
            return deleted_count
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete old records: {e}")
            return 0
    
    async def delete_failed_records(self, days: int = 7) -> int:
        """Delete failed records older than specified days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            deleted_count = self.db.query(AudioRecord)\
                .filter(
                    and_(
                        AudioRecord.status == "failed",
                        AudioRecord.created_at < cutoff_date
                    )
                )\
                .delete()
            await self.db.commit()
            
            logger.info(f"Deleted {deleted_count} failed records older than {days} days")
            return deleted_count
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete failed records: {e}")
            return 0
    
    # ---------------- STATISTICS ----------------
    async def get_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics for audio records"""
        try:
            query = self.db.query(AudioRecord)
            if user_id:
                query = query.filter(AudioRecord.user_id == user_id)
            
            # Basic stats
            total_records = query.count()
            
            # Voice cloning stats
            voice_cloning_count = query.filter(AudioRecord.is_voice_cloning == True).count()
            
            # Status distribution
            status_stats = {}
            for status in ['pending', 'processing', 'completed', 'failed']:
                count = query.filter(AudioRecord.status == status).count()
                if count > 0:
                    status_stats[status] = count
            
            # Voice distribution
            voice_stats = self.db.query(
                AudioRecord.voice_id,
                func.count(AudioRecord.id).label('count')
            )
            if user_id:
                voice_stats = voice_stats.filter(AudioRecord.user_id == user_id)
            voice_stats = voice_stats.group_by(AudioRecord.voice_id)\
                .order_by(func.count(AudioRecord.id).desc())\
                .limit(10)\
                .all()
            
            # Duration stats
            duration_result = query.filter(
                AudioRecord.duration_seconds.isnot(None)
            ).with_entities(
                func.sum(AudioRecord.duration_seconds).label('total_duration'),
                func.avg(AudioRecord.duration_seconds).label('avg_duration'),
                func.max(AudioRecord.duration_seconds).label('max_duration'),
                func.min(AudioRecord.duration_seconds).label('min_duration')
            ).first()
            
            # Daily records (last 7 days)
            daily_stats = []
            for i in range(7):
                date = datetime.now().date() - timedelta(days=i)
                start_date = datetime.combine(date, datetime.min.time())
                end_date = datetime.combine(date, datetime.max.time())
                
                count = self.db.query(AudioRecord)\
                    .filter(AudioRecord.created_at.between(start_date, end_date))
                if user_id:
                    count = count.filter(AudioRecord.user_id == user_id)
                count = count.count()
                
                daily_stats.append({
                    "date": date.isoformat(),
                    "count": count
                })
            
            return {
                "total_records": total_records,
                "voice_cloning_records": voice_cloning_count,
                "regular_tts_records": total_records - voice_cloning_count,
                "status_distribution": status_stats,
                "top_voices": [
                    {"voice_id": voice_id, "count": count}
                    for voice_id, count in voice_stats
                ],
                "duration_stats": {
                    "total_seconds": float(duration_result[0] or 0),
                    "total_hours": float(duration_result[0] or 0) / 3600,
                    "average_seconds": float(duration_result[1] or 0),
                    "max_seconds": float(duration_result[2] or 0),
                    "min_seconds": float(duration_result[3] or 0),
                },
                "daily_records": daily_stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}
    
    async def get_cache_hit_rate(self, user_id: Optional[str] = None) -> float:
        """Calculate cache hit rate"""
        try:
            query = self.db.query(AudioRecord)
            if user_id:
                query = query.filter(AudioRecord.user_id == user_id)
            
            total = query.count()
            if total == 0:
                return 0.0
            
            cached = query.filter(AudioRecord.from_cache == True).count()
            return (cached / total) * 100
            
        except Exception as e:
            logger.error(f"Failed to get cache hit rate: {e}")
            return 0.0
    
    # ---------------- SEARCH ----------------
    async def search_by_text(
        self, 
        search_text: str, 
        user_id: Optional[str] = None,
        limit: int = 50
    ) -> List[AudioRecord]:
        """Search records by text content"""
        try:
            query = self.db.query(AudioRecord)\
                .filter(AudioRecord.text.ilike(f'%{search_text}%'))
            
            if user_id:
                query = query.filter(AudioRecord.user_id == user_id)
            
            records = query.order_by(desc(AudioRecord.created_at))\
                .limit(limit)\
                .all()
            
            return records
        except Exception as e:
            logger.error(f"Failed to search records: {e}")
            return []
    
    # ---------------- UPSERT ----------------
    async def get_or_create(
        self, 
        filename: str, 
        default_data: Dict[str, Any]
    ) -> tuple[AudioRecord, bool]:
        """Get existing record by filename or create new one"""
        try:
            existing = await self.get_by_filename(filename)
            if existing:
                return existing, False
            
            record = await self.create(default_data)
            return record, True
        except Exception as e:
            logger.error(f"Failed to get or create record: {e}")
            raise