import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

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

    # HASHED refresh token - never store plaintext token
    token_hash = Column(
        String(255),
        nullable=False,
        unique=True,
    )

    revoked = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    expires_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    # "refresh" | "reset"
    type = Column(
        String(20),
        nullable=False,
        default="refresh",
    )

    # ---------------- Relationships ----------------

    user = relationship(
        "User",
        back_populates="refresh_tokens",
        lazy="joined",
    )


# ---------------- Indexes ----------------

Index(
    "idx_refresh_token_user_active",
    RefreshToken.user_id,
    RefreshToken.revoked,
)