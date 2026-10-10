from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.domain.models.user import User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def create(
        self,
        email: str,
        name: str,
        password_hash: str | None = None,
        social_uid: str | None = None,
        provider: str | None = None,
        email_verified: bool = False
    ) -> User:
        user = User(
            email=email,
            password_hash=password_hash,
            name=name,
            provider=provider,
            social_uid=social_uid,
            email_verified=email_verified
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def get_by_social_uid(self, social_uid: str) -> User | None:
        stmt = select(User).where(User.social_uid == social_uid)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def update_social(
        self,
       user_id: UUID,
        social_uid: str,
        provider: str,
    ) -> None:
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(
                social_uid=social_uid,
                # provider=provider,
            )
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def update_password(self, user_id: UUID , password_hash: str):
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(password_hash=password_hash)
        )
        await self.db.commit()

    async def mark_email_verified(self,user_id: UUID ):
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(email_verified=True)
            .returning(User)
        )

        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.scalar_one_or_none()