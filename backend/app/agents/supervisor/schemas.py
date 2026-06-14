from typing import Any

from pydantic import BaseModel


class SupervisorResponse(BaseModel):

    cart: dict

    urgency: dict

    reasoning: str

    conversation_reply: str = ""
    """User-facing natural language response (no JSON, no technical data)."""

    eco_alternative: dict | None = None

    metadata: dict[str, Any] = {}
