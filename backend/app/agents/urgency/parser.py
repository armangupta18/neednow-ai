import json

from pydantic import ValidationError

from app.agents.urgency.schemas import (
    UrgencyResponse,
)

from app.agents.urgency.exceptions import (
    UrgencyParsingException,
    UrgencyValidationException,
)


class UrgencyParser:

    @staticmethod
    def parse(text: str) -> UrgencyResponse:

        try:

            cleaned = (
                text.replace("```json", "")
                .replace("```", "")
                .strip()
            )

            data = json.loads(cleaned)

        except Exception as e:

            raise UrgencyParsingException(
                str(e)
            )

        try:

            return UrgencyResponse(
                **data
            )

        except ValidationError as e:

            raise UrgencyValidationException(
                str(e)
            )