from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import desc, select

from app.domain.models.media_record import MediaRecord
from app.infrastructure.repositories.base import BaseRepository


class VideoRepository(BaseRepository):
    """
    Repository for generated media records.

    Supports:
    - Text -> Video
    - Image -> Video
    - Video -> Video
    - Video + Reference Images -> Video
    - Text -> Image
    - Image -> Image

    Generation lifecycle:
        pending
            -> processing
                -> completed
                -> failed
    """

    # ============================================================
    # CREATE
    # ============================================================

    async def create(
        self,
        record: MediaRecord,
    ) -> MediaRecord:
        self.db.add(record)

        await self.db.commit()
        await self.db.refresh(record)

        return record

    # ============================================================
    # CREATE GENERATION
    # ============================================================

    async def create_generation(
        self,
        *,
        user_id: UUID ,
        generation_type: str,
        media_type: str,
        provider: str = "runway",
        status: str = "pending",
        prompt: Optional[str] = None,
        style: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        duration: Optional[float] = None,
        output_url: Optional[str] = None,
        output_filename: Optional[str] = None,
        voice_url: Optional[str] = None,
        source_video_url: Optional[str] = None,
        source_image_url: Optional[str] = None,
        source_image_urls: Optional[List[str]] = None,
        reference_image_urls: Optional[List[str]] = None,
        error_message: Optional[str] = None,
        extra_data: Optional[dict] = None,
    ) -> MediaRecord:
        """
        Create a new generation history record.

        Usually created before calling Runway:

            pending -> processing -> completed

        If generation fails:

            pending/processing -> failed
        """

        record = MediaRecord(
            user_id=user_id,
            generation_type=generation_type,
            media_type=media_type,
            provider=provider,
            status=status,
            prompt=prompt,
            style=style,
            aspect_ratio=aspect_ratio,
            duration=duration,
            output_url=output_url,
            output_filename=output_filename,
            voice_url=voice_url,
            source_video_url=source_video_url,
            source_image_url=source_image_url,
            source_image_urls=source_image_urls or [],
            reference_image_urls=reference_image_urls or [],
            error_message=error_message,
            extra_data=extra_data or {},
        )

        return await self.create(record)

    # ============================================================
    # GET BY ID
    # ============================================================

    async def get_by_id(
        self,
        record_id: UUID,
    ) -> Optional[MediaRecord]:
        result = await self.db.execute(
            select(MediaRecord).where(
                MediaRecord.id == record_id
            )
        )

        return result.scalar_one_or_none()

    # ============================================================
    # GET BY ID + USER
    # ============================================================

    async def get_by_id_and_user(
        self,
        record_id: UUID,
        user_id: UUID,
    ) -> Optional[MediaRecord]:
        result = await self.db.execute(
            select(MediaRecord).where(
                MediaRecord.id == record_id,
                MediaRecord.user_id == user_id,
            )
        )

        return result.scalar_one_or_none()

    # ============================================================
    # LIST ALL BY USER
    # ============================================================

    async def list_by_user(
        self,
        user_id: UUID,
    ) -> List[MediaRecord]:
        result = await self.db.execute(
            select(MediaRecord)
            .where(
                MediaRecord.user_id == user_id
            )
            .order_by(
                desc(MediaRecord.created_at)
            )
        )

        return list(result.scalars().all())

    # ============================================================
    # LIST VIDEOS BY USER
    # ============================================================

    async def list_videos_by_user(
        self,
        user_id: UUID,
    ) -> List[MediaRecord]:
        result = await self.db.execute(
            select(MediaRecord)
            .where(
                MediaRecord.user_id == user_id,
                MediaRecord.media_type == "video",
            )
            .order_by(
                desc(MediaRecord.created_at)
            )
        )

        return list(result.scalars().all())

    # ============================================================
    # LIST IMAGES BY USER
    # ============================================================

    async def list_images_by_user(
        self,
        user_id: UUID,
    ) -> List[MediaRecord]:
        result = await self.db.execute(
            select(MediaRecord)
            .where(
                MediaRecord.user_id == user_id,
                MediaRecord.media_type == "image",
            )
            .order_by(
                desc(MediaRecord.created_at)
            )
        )

        return list(result.scalars().all())

    # ============================================================
    # LIST BY GENERATION TYPE
    # ============================================================

    async def list_by_generation_type(
        self,
        user_id: UUID,
        generation_type: str,
    ) -> List[MediaRecord]:
        result = await self.db.execute(
            select(MediaRecord)
            .where(
                MediaRecord.user_id == user_id,
                MediaRecord.generation_type == generation_type,
            )
            .order_by(
                desc(MediaRecord.created_at)
            )
        )

        return list(result.scalars().all())

    # ============================================================
    # LIST BY STATUS
    # ============================================================

    async def list_by_status(
        self,
        user_id: UUID,
        status: str,
    ) -> List[MediaRecord]:
        result = await self.db.execute(
            select(MediaRecord)
            .where(
                MediaRecord.user_id == user_id,
                MediaRecord.status == status,
            )
            .order_by(
                desc(MediaRecord.created_at)
            )
        )

        return list(result.scalars().all())

    # ============================================================
    # UPDATE STATUS
    # ============================================================

    async def update_status(
        self,
        record_id: UUID,
        status: str,
    ) -> Optional[MediaRecord]:
        record = await self.get_by_id(record_id)

        if not record:
            return None

        record.status = status
        record.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(record)

        return record

    # ============================================================
    # MARK PROCESSING
    # ============================================================

    async def mark_processing(
        self,
        record_id: UUID,
    ) -> Optional[MediaRecord]:
        return await self.update_status(
            record_id=record_id,
            status="processing",
        )

    # ============================================================
    # MARK COMPLETED
    # ============================================================

    async def mark_done(
        self,
        record_id: UUID,
        *,
        output_url: str,
        output_filename: Optional[str] = None,
        duration: Optional[float] = None,
        voice_url: Optional[str] = None,
        source_video_url: Optional[str] = None,
        source_image_url: Optional[str] = None,
        source_image_urls: Optional[List[str]] = None,
        reference_image_urls: Optional[List[str]] = None,
        extra_data: Optional[dict] = None,
    ) -> Optional[MediaRecord]:
        record = await self.get_by_id(record_id)

        if not record:
            return None

        record.status = "completed"
        record.output_url = output_url

        if output_filename is not None:
            record.output_filename = output_filename

        if duration is not None:
            record.duration = duration

        if voice_url is not None:
            record.voice_url = voice_url

        if source_video_url is not None:
            record.source_video_url = source_video_url

        if source_image_url is not None:
            record.source_image_url = source_image_url

        if source_image_urls is not None:
            record.source_image_urls = source_image_urls

        if reference_image_urls is not None:
            record.reference_image_urls = reference_image_urls

        if extra_data is not None:
            record.extra_data = extra_data

        record.error_message = None
        record.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(record)

        return record

    # ============================================================
    # MARK FAILED
    # ============================================================

    async def mark_failed(
        self,
        record_id: UUID,
        error_message: str,
    ) -> Optional[MediaRecord]:
        record = await self.get_by_id(record_id)

        if not record:
            return None

        record.status = "failed"
        record.error_message = error_message
        record.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(record)

        return record

    # ============================================================
    # UPDATE EXTRA DATA
    # ============================================================

    async def update_extra_data(
        self,
        record_id: UUID,
        extra_data: dict,
    ) -> Optional[MediaRecord]:
        record = await self.get_by_id(record_id)

        if not record:
            return None

        record.extra_data = extra_data
        record.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(record)

        return record

    # ============================================================
    # DELETE
    # ============================================================

    async def delete(
        self,
        record_id: UUID,
        user_id: Optional[UUID] = None,
    ) -> bool:
        if user_id is not None:
            record = await self.get_by_id_and_user(
                record_id=record_id,
                user_id=user_id,
            )
        else:
            record = await self.get_by_id(
                record_id
            )

        if not record:
            return False

        await self.db.delete(record)
        await self.db.commit()

        return True