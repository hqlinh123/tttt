import uuid
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base
from sqlalchemy.dialects.postgresql import UUID

class MediaRecord(Base):
    __tablename__ = "media_records"

    id = Column(
            UUID(as_uuid=True),
            primary_key=True,
            default=uuid.uuid4,
            index=True,
        )
    
    user_id = Column(
            UUID(as_uuid=True),
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    generation_type = Column(
        String(50),
        nullable=False,
        index=True,
    )

    media_type = Column(
        String(20),
        nullable=False,
        index=True,
    )

    provider = Column(
        String(30),
        nullable=False,
        default="runway",
    )

    status = Column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )

    prompt = Column(Text, nullable=True)
    style = Column(String(255), nullable=True)
    aspect_ratio = Column(String(20), nullable=True)

    duration = Column(Float, nullable=True)

    output_url = Column(Text, nullable=True)
    output_filename = Column(String(500), nullable=True)

    voice_url = Column(Text, nullable=True)

    source_video_url = Column(Text, nullable=True)
    source_image_url = Column(Text, nullable=True)

    source_image_urls = Column(
        JSON,
        nullable=False,
        default=list,
    )

    reference_image_urls = Column(
        JSON,
        nullable=False,
        default=list,
    )

    error_message = Column(Text, nullable=True)

    extra_data = Column(
        JSON,
        nullable=False,
        default=dict,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user = relationship(
        "User",
        back_populates="media_records",
    )