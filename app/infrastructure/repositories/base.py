from sqlalchemy.ext.asyncio import AsyncSession

class BaseRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add(self, entity):
        self.db.add(entity)
