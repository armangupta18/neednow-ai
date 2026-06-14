from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.memory.memory_manager import MemoryManager
from app.memory.memory_repository import MemoryRepository


def get_memory_manager(
    db: AsyncSession = Depends(get_db),
) -> MemoryManager:
    return MemoryManager(MemoryRepository(db))
