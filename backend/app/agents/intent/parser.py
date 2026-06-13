import json

from pydantic import ValidationError

from app.agents.intent.schemas import IntentResponse
from app.agents.intent.exceptions import (
    IntentParsingException,
    IntentValidationException,
)


class IntentParser:

    @staticmethod
    def parse(
        response_text: str,
    ) -> IntentResponse:

        try:

            cleaned = response_text.strip()

            if cleaned.startswith("```json"):
                cleaned = cleaned.replace(
                    "```json",
                    ""
                )

            cleaned = cleaned.replace(
                "```",
                ""
            )

            data = json.loads(cleaned)

        except Exception as e:
            raise IntentParsingException(
                f"Unable to parse JSON: {e}"
            )

        try:

            return IntentResponse(
                **data
            )

        except ValidationError as e:
            raise IntentValidationException(
                str(e)
            )