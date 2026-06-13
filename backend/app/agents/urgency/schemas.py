from enum import Enum

from pydantic import BaseModel, Field


class UrgencyLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class UrgencyResponse(BaseModel):

    urgency: UrgencyLevel

    score: int = Field(
        ge=0,
        le=100,
    )

    explanation: str