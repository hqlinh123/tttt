import hashlib
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.domain.models.token import RefreshToken


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class TokenRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ---------------- SAVE REFRESH ----------------
    async def save_refresh_token(
        self, user_id: UUID | str, refresh_token: str
    ):
        token = RefreshToken(
            user_id=user_id,
            token_hash=hash_token(refresh_token),
            type="refresh",
            expires_at=None,  # or set expiry if needed
        )
        self.db.add(token)
        await self.db.commit()

    # ---------------- SAVE RESET ----------------
    async def save_reset_token(
        self, user_id: UUID, token: str
    ):
        token_obj = RefreshToken(
            user_id=user_id,
            token_hash=hash_token(token),  # ✅ hash it!
            type="reset",
            expires_at=datetime.utcnow() + timedelta(minutes=15),
        )
        self.db.add(token_obj)
        await self.db.commit()

    # ---------------- VALIDATE ----------------
    async def is_valid(
        self, token: str, token_type: str = "refresh"
    ) -> bool:
        token_hash = hash_token(token)

        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.type == token_type,
                RefreshToken.revoked.is_(False),
            )
        )
        token_obj = result.scalar_one_or_none()

        if not token_obj:
            return False

        # check expiry
        if token_obj.expires_at and token_obj.expires_at < datetime.utcnow():
            return False

        return True

    # ---------------- REVOKE ----------------
    async def revoke(self, token: str):
        token_hash = hash_token(token)

        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash
            )
        )
        token_obj = result.scalar_one_or_none()

        if token_obj:
            token_obj.revoked = True
            await self.db.commit()
            
    async def save_otp(self, user_id: UUID, otp: str):
        token = RefreshToken(
            user_id=user_id,
            token_hash=hash_token(otp),
            type="otp",
            expires_at=datetime.utcnow() + timedelta(minutes=5),
        )
        self.db.add(token)
        await self.db.commit()

    async def verify_otp(self, user_id: UUID , otp: str) -> bool:
        token_hash = hash_token(otp)

        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.token_hash == token_hash,
                RefreshToken.type == "otp",
                RefreshToken.revoked.is_(False),
            )
        )
        token = result.scalar_one_or_none()

        if not token:
            return False

        if token.expires_at < datetime.utcnow():
            return False

        # single-use
        token.revoked = True
        await self.db.commit()

        return True

    async def count_recent_otp(self, user_id: UUID ) -> int:
        # count OTP created in last 5 minutes
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.type == "otp",
                RefreshToken.expires_at > datetime.utcnow(),
            )
        )
        return len(result.scalars().all())