from uuid import UUID

from app.memory.schemas import UserMemory
from app.memory.memory_repository import MemoryRepository


class MemoryManager:

    def __init__(self, repository: MemoryRepository):
        self.repository = repository

    async def save_memory(
        self,
        user_id: UUID,
        memory: UserMemory,
    ) -> dict:

        user = await self.repository.get_user(user_id)

        if not user:
            raise ValueError("User not found")

        user.memory = memory.model_dump()

        await self.repository.save(user)

        return user.memory

    async def retrieve_memory(
        self,
        user_id: UUID,
    ) -> UserMemory:

        user = await self.repository.get_user(user_id)

        if not user:
            raise ValueError("User not found")

        return UserMemory(
            **(user.memory or {})
        )

    async def update_memory(
        self,
        user_id: UUID,
        updates: dict,
    ) -> UserMemory:

        user = await self.repository.get_user(user_id)

        if not user:
            raise ValueError("User not found")

        existing = user.memory or {}

        existing.update(updates)

        user.memory = existing

        await self.repository.save(user)

        return UserMemory(**existing)