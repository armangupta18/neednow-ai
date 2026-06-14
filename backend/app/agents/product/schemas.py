from uuid import UUID
from typing import List, Optional

from pydantic import BaseModel, Field


class ProductCandidate(BaseModel):

    product_id: UUID

    title: str

    category: str

    price: float

    similarity_score: float

    ranking_score: float

    reason: Optional[str] = Field(
        default=None,
        description="Why this product was recommended for the user's situation",
    )

    priority: Optional[int] = Field(
        default=None,
        ge=1,
        le=4,
        description="Recommendation priority (1=highest, 4=lowest)",
    )


class ProductResponse(BaseModel):

    top_products: List[ProductCandidate]

    bundle_products: List[ProductCandidate]

    confidence: float
