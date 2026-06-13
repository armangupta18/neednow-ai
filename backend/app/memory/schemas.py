from typing import List, Optional

from pydantic import BaseModel, Field


class UserMemory(BaseModel):
    dietary_preferences: List[str] = Field(default_factory=list)

    preferred_brands: List[str] = Field(default_factory=list)

    budget_level: Optional[str] = None

    family_size: Optional[int] = None

    purchase_patterns: List[str] = Field(default_factory=list)

    sustainability_score: float = 0.0