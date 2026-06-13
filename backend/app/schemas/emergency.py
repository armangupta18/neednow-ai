from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.agents.urgency.schemas import UrgencyLevel


class EmergencyAnalyzeRequest(BaseModel):
    """Request payload for emergency urgency analysis."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    user_id: UUID
    text: str = Field(..., min_length=1, max_length=5000)
    user_context: dict[str, Any] = Field(default_factory=dict)


class EmergencyAnalyzeResponse(BaseModel):
    """Urgency analysis result with emergency classification."""

    model_config = ConfigDict(extra="forbid")

    user_id: UUID
    urgency: UrgencyLevel
    score: int = Field(ge=0, le=100)
    explanation: str
    is_emergency: bool
    escalation_recommended: bool


class EmergencyEscalateRequest(BaseModel):
    """Request payload to trigger the emergency escalation workflow."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    user_id: UUID
    text: str = Field(..., min_length=1, max_length=5000)
    user_context: dict[str, Any] = Field(default_factory=dict)
    contact_phone: str | None = Field(default=None, max_length=30)


class EmergencyEscalateResponse(BaseModel):
    """Emergency workflow escalation result."""

    model_config = ConfigDict(extra="forbid")

    user_id: UUID
    escalated: bool
    urgency: UrgencyLevel
    score: int = Field(ge=0, le=100)
    workflow_id: str
    message: str
    actions: list[str] = Field(default_factory=list)


class EmergencyHealthResponse(BaseModel):
    """Health status for the emergency subsystem."""

    model_config = ConfigDict(extra="forbid")

    status: str
    urgency_agent: str
    emergency_agent: str
