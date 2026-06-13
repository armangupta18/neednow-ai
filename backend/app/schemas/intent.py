from uuid import UUID

from pydantic import BaseModel, Field


class IntentRequest(BaseModel):

    text: str = Field(
        min_length=1,
        max_length=5000,
    )

    user_id: UUID