from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MessageRole(str, Enum):
    USER = "user"
    SYSTEM = "system"
    ASSISTANT = "assistant"


class AgentMessage(BaseModel):
    """Shared message schema for agent conversations and orchestration."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    user_id: UUID = Field(..., description="Owner of the conversation")
    session_id: UUID = Field(..., description="Conversation session identifier")
    content: str = Field(..., min_length=1, description="Message body")
    role: MessageRole = Field(..., description="Message author role")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional structured context for routing, tracing, or agent state",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when the message was created",
    )
