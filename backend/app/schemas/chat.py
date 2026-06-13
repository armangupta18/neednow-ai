from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.agents.shared.message import AgentMessage


class ChatRequest(BaseModel):
    """Incoming chat message for the supervisor pipeline."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    user_id: UUID
    message: str = Field(..., min_length=1, max_length=5000)
    session_id: UUID | None = Field(
        default=None,
        description="Existing session identifier; a new session is created when omitted",
    )


class ChatResponse(BaseModel):
    """Chat turn response with assistant reply and recommendation payload."""

    model_config = ConfigDict(extra="forbid")

    session_id: UUID
    user_message: AgentMessage
    assistant_message: AgentMessage
    cart: dict[str, Any]
    urgency: dict[str, Any]
    reasoning: str
    eco_alternative: dict[str, Any] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatHistoryResponse(BaseModel):
    """Conversation history for a session."""

    model_config = ConfigDict(extra="forbid")

    session_id: UUID
    user_id: UUID
    messages: list[AgentMessage] = Field(default_factory=list)
