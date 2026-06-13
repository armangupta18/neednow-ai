from uuid import UUID
from typing import List

from pydantic import BaseModel


class EcoAlternative(BaseModel):

    original_product_id: UUID

    original_product_name: str

    alternative_product_id: UUID

    alternative_product_name: str

    carbon_saved: float

    price_difference: float

    sustainability_score: float


class SustainabilityResponse(BaseModel):

    eco_alternatives: List[EcoAlternative]

    total_carbon_saved: float

    overall_sustainability_score: float