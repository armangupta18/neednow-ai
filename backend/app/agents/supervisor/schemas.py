from typing import Any

from pydantic import BaseModel


class SupervisorResponse(BaseModel):

    cart: dict

    urgency: dict

    reasoning: str

    eco_alternative: dict | None = None

    metadata: dict[str, Any] = {}