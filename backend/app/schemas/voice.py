from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class VoiceTranscribeResponse(BaseModel):
    """Response from audio transcription."""

    model_config = ConfigDict(extra="forbid")

    user_id: UUID
    text: str = Field(..., min_length=1, description="Transcribed text")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Transcription confidence score"
    )
    language: str = Field(default="en", description="Detected language code")
    duration_seconds: float = Field(default=0.0, description="Audio duration in seconds")


class VoiceChatRequest(BaseModel):
    """Request for voice chat processing."""

    model_config = ConfigDict(extra="forbid")

    user_id: UUID
    session_id: UUID | None = Field(
        None, description="Existing session; new session created if omitted"
    )
    language: str = Field(default="en", description="Language code for transcription")


class VoiceChatResponse(BaseModel):
    """Voice chat response with transcription and chat result."""

    model_config = ConfigDict(extra="forbid")

    session_id: UUID
    user_id: UUID
    transcribed_text: str = Field(
        ..., min_length=1, description="Original transcribed text"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Transcription confidence"
    )
    assistant_reply: str = Field(..., description="Assistant's text response")
    cart: dict = Field(default_factory=dict, description="Cart state from chat response")
    urgency: dict | None = Field(
        None, description="Urgency analysis from supervisor"
    )
    eco_alternative: dict | None = Field(
        None, description="Sustainability alternative recommendation"
    )
    metadata: dict = Field(default_factory=dict, description="Additional metadata")
