from uuid import UUID
from typing import List

from pydantic import BaseModel


class ProductCandidate(BaseModel):

    product_id: UUID

    title: str

    category: str

    price: float

    similarity_score: float

    ranking_score: float


class ProductResponse(BaseModel):

    top_products: List[ProductCandidate]

    bundle_products: List[ProductCandidate]

    confidence: float