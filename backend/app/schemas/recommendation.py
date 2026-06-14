"""Recommendation schemas for NeedNow AI.

Pydantic v2 request and response models for the recommendation system.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RecommendationBase(BaseModel):
    """Base fields shared across recommendation schemas."""

    product_id: str
    product_name: str
    score: float = Field(..., ge=0)
    reason: str
    agent_source: str


class RecommendationResponse(RecommendationBase):
    """Single recommendation response (ORM-compatible)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    session_id: str
    created_at: datetime


class RecommendationListResponse(BaseModel):
    """Paginated list of recommendations."""

    success: bool = True
    count: int
    recommendations: list[RecommendationResponse]


class RecommendationRequest(BaseModel):
    """Request to generate recommendations."""

    user_id: str
    session_id: str
    query: str


class RecommendationCreate(BaseModel):
    """Payload for creating a new recommendation record."""

    user_id: str
    session_id: str
    product_id: str
    product_name: str
    score: float = Field(..., ge=0)
    reason: str
    agent_source: str
