from typing import Any, List, Optional

from pydantic import BaseModel


class ProductReasoning(BaseModel):
    product_name: str
    reason: str


class SupervisorResponse(BaseModel):

    cart: dict

    urgency: Optional[dict] = None

    reasoning: str

    product_reasonings: List[ProductReasoning] = []
    """Per-product reasoning items (one entry per top recommended product)."""

    conversation_reply: str = ""
    """User-facing natural language response (no JSON, no technical data)."""

    eco_alternative: Optional[dict] = None

    metadata: dict[str, Any] = {}
