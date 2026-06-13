from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class MemoryRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user(self, user_id: UUID):

        stmt = select(User).where(User.id == user_id)

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()

    async def save(self, user: User):

        self.db.add(user)

        await self.db.commit()

        await self.db.refresh(user)

        return user