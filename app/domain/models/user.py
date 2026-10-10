from sqlalchemy import Column, Integer, String, Boolean
from app.db.base import Base
from sqlalchemy.orm import relationship

import uuid
from sqlalchemy.dialects.postgresql import UUID

class User(Base):
    __tablename__ = "users"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255))
    is_active = Column(Boolean, default=True)
    media_records = relationship(
        "MediaRecord",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    refresh_tokens = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    social_uid = Column(String, unique=True, index=True, nullable=True)
    provider = Column(String, nullable=True, default=None),
    email_verified = Column(Boolean, default=False)
