from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.agents.sustainability.schemas import EcoAlternative


class SustainabilityAnalyzeRequest(BaseModel):
    """Request payload for generating a sustainability report."""

    model_config = ConfigDict(extra="forbid")

    product_ids: list[UUID] = Field(..., min_length=1)


class SustainabilityRecommendRequest(BaseModel):
    """Request payload for eco-friendly alternative recommendations."""

    model_config = ConfigDict(extra="forbid")

    product_ids: list[UUID] = Field(..., min_length=1)


class SustainabilityReportResponse(BaseModel):
    """Full sustainability analysis report."""

    model_config = ConfigDict(extra="forbid")

    eco_alternatives: list[EcoAlternative] = Field(default_factory=list)
    total_carbon_saved: float
    overall_sustainability_score: float


class SustainabilityRecommendResponse(BaseModel):
    """Eco-friendly alternative recommendations."""

    model_config = ConfigDict(extra="forbid")

    recommendations: list[EcoAlternative] = Field(default_factory=list)
    total_carbon_saved: float
    overall_sustainability_score: float


class ProductEcoScoreResponse(BaseModel):
    """Eco score for a single product."""

    model_config = ConfigDict(extra="forbid")

    product_id: UUID
    product_name: str
    category: str
    sustainability_score: float = Field(ge=0, le=100)
