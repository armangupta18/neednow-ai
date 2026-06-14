"""Chat schemas for NeedNow AI.

Defines Pydantic v2 request and response models for the conversational
AI pipeline (supervisor → intent → urgency → product → sustainability).

Exports:
    - ChatRequest
    - ChatResponse
    - ChatHistoryRequest
    - ChatHistoryResponse
    - ChatStreamEvent
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.agents.shared.message import AgentMessage


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ChatEventType(str, Enum):
    """Types of streaming chat events."""

    MESSAGE = "message"
    THINKING = "thinking"
    PRODUCT = "product"
    CART_UPDATE = "cart_update"
    ECO_ALERT = "eco_alert"
    ERROR = "error"
    DONE = "done"


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------


class ChatRequest(BaseModel):
    """Incoming chat message for the supervisor pipeline.

    Validates user input and optional session context before
    routing to the multi-agent orchestration system.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        json_schema_extra={
            "examples": [
                {
                    "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "message": "I need baby formula urgently",
                    "session_id": None,
                }
            ]
        },
    )

    user_id: UUID = Field(
        ...,
        description="UUID of the authenticated user",
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="User's chat message text",
    )
    session_id: UUID | None = Field(
        default=None,
        description="Existing session ID; omit to start a new conversation",
    )
    context: dict[str, Any] | None = Field(
        default=None,
        description="Optional client-side context (device, location, etc.)",
    )

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, v: str) -> str:
        """Ensure message is not just whitespace."""
        if not v.strip():
            raise ValueError("Message must contain non-whitespace characters")
        return v.strip()


class ChatHistoryRequest(BaseModel):
    """Request to retrieve conversation history."""

    model_config = ConfigDict(extra="forbid")

    user_id: UUID = Field(..., description="UUID of the user")
    session_id: UUID = Field(..., description="Session to retrieve history for")
    limit: int = Field(
        default=50,
        ge=1,
        le=200,
        description="Maximum messages to return",
    )
    before: datetime | None = Field(
        default=None,
        description="Return messages before this timestamp (for pagination)",
    )


# ---------------------------------------------------------------------------
# Response Models
# ---------------------------------------------------------------------------


class CartSnapshot(BaseModel):
    """Lightweight cart state included in chat responses."""

    model_config = ConfigDict(extra="allow")

    cart_id: UUID | None = None
    total_amount: float = 0.0
    item_count: int = 0
    items: list[dict[str, Any]] = Field(default_factory=list)


class UrgencySnapshot(BaseModel):
    """Urgency assessment included in chat responses."""

    model_config = ConfigDict(extra="allow")

    level: str = Field(default="normal", description="Urgency level")
    score: float = Field(default=0.0, ge=0.0, le=1.0, description="Urgency score")
    reasoning: str = Field(default="", description="Why this urgency was assigned")


class EcoAlternative(BaseModel):
    """Eco-friendly alternative suggestion."""

    model_config = ConfigDict(extra="allow")

    product_id: UUID | None = None
    product_name: str = ""
    eco_score: float = Field(default=0.0, ge=0.0, le=100.0)
    carbon_saved_kg: float = 0.0
    reason: str = ""


class ChatResponse(BaseModel):
    """Chat turn response with assistant reply and recommendation payload.

    Returned after the full supervisor pipeline processes a user message.
    """

    model_config = ConfigDict(extra="forbid")

    session_id: UUID = Field(..., description="Active session identifier")
    user_message: AgentMessage = Field(
        ..., description="Echoed user message with metadata"
    )
    assistant_message: AgentMessage = Field(
        ..., description="AI assistant reply"
    )
    cart: CartSnapshot | dict[str, Any] = Field(
        default_factory=dict,
        description="Current cart state after this turn",
    )
    urgency: UrgencySnapshot | dict[str, Any] = Field(
        default_factory=dict,
        description="Urgency assessment for this turn",
    )
    reasoning: str = Field(
        default="",
        description="Supervisor agent's reasoning chain",
    )
    eco_alternative: EcoAlternative | dict[str, Any] | None = Field(
        default=None,
        description="Suggested eco-friendly alternative (if applicable)",
    )
    recommended_products: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Product recommendations generated this turn",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional response metadata (timing, model info, etc.)",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Response generation timestamp",
    )


class ChatHistoryResponse(BaseModel):
    """Conversation history for a session."""

    model_config = ConfigDict(extra="forbid")

    session_id: UUID = Field(..., description="Session identifier")
    user_id: UUID = Field(..., description="User identifier")
    messages: list[AgentMessage] = Field(
        default_factory=list,
        description="Ordered list of conversation messages",
    )
    total_messages: int = Field(
        default=0,
        ge=0,
        description="Total message count in the session",
    )
    has_more: bool = Field(
        default=False,
        description="Whether more messages exist before the returned window",
    )


# ---------------------------------------------------------------------------
# Streaming Models
# ---------------------------------------------------------------------------


class ChatStreamEvent(BaseModel):
    """Server-Sent Event payload for streaming chat responses.

    Used with SSE or WebSocket connections for real-time UI updates
    as the agent pipeline processes a request.
    """

    model_config = ConfigDict(extra="forbid")

    event_type: ChatEventType = Field(
        ..., description="Type of streaming event"
    )
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Event payload",
    )
    session_id: UUID | None = Field(
        default=None,
        description="Session this event belongs to",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
