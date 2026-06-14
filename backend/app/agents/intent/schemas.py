from typing import Optional, Literal

from pydantic import BaseModel, Field


class IntentResponse(BaseModel):

    intent: str = Field(
        ...,
        description="Concise intent label (e.g., first_aid, pain_relief, baby_care)",
    )

    urgency: Literal[
        "low",
        "medium",
        "high",
        "critical",
    ]

    category: str = Field(
        ...,
        description="Shopping category",
    )

    keywords: list[str] = Field(
        default_factory=list,
        description="Product search keywords relevant to the situation",
    )

    budget: Optional[float] = None

    people_count: Optional[int] = None

    confidence: float = Field(
        ge=0,
        le=1,
    )
