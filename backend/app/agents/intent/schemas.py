from typing import Optional, Literal

from pydantic import BaseModel, Field


class IntentResponse(BaseModel):

    category: str = Field(
        ...,
        description="Shopping category"
    )

    urgency: Literal[
        "low",
        "medium",
        "high",
        "critical"
    ]

    budget: Optional[float] = None

    people_count: Optional[int] = None

    confidence: float = Field(
        ge=0,
        le=1,
    )