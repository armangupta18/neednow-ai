from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.memory.schemas import UserMemory


class StoreMemoryRequest(BaseModel):
    """Request payload for persisting user memory."""

    model_config = ConfigDict(extra="forbid")

    user_id: UUID
    memory: UserMemory


class MemoryResponse(BaseModel):
    """User memory retrieval response."""

    model_config = ConfigDict(extra="forbid")

    user_id: UUID
    memory: UserMemory


class ClearMemoryResponse(BaseModel):
    """Confirmation response after clearing user memory."""

    model_config = ConfigDict(extra="forbid")

    user_id: UUID
    cleared: bool = True
    message: str = Field(default="Memory cleared successfully")
