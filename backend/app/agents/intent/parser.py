import json
import logging

from pydantic import ValidationError

from app.agents.intent.exceptions import (
    IntentParsingException,
    IntentValidationException,
)
from app.agents.intent.schemas import IntentResponse
from app.utils.helpers import HelperUtils

logger = logging.getLogger(__name__)


class IntentParser:

    @staticmethod
    def parse(
        response_text: str,
        user_prompt: str = "",
    ) -> IntentResponse:
        """Parse raw response from Gemini into a validated IntentResponse."""
        data = HelperUtils.extract_json(response_text)

        if not isinstance(data, dict):
            raise IntentParsingException("Could not parse JSON object from model response.")

        try:
            return IntentResponse(**data)
        except ValidationError as exc:
            raise IntentValidationException(f"Invalid intent response structure: {exc}") from exc

    @staticmethod
    def _fallback_intent(text: str) -> IntentResponse:
        text_lower = text.lower()
        if any(w in text_lower for w in ["cut", "bleed", "wound", "bandage", "first aid"]):
            category, intent = "medical", "first_aid"
            keywords = ["bandage", "antiseptic", "gauze"]
        elif any(w in text_lower for w in ["pain", "headache", "fever", "medicine"]):
            category, intent = "medical", "pain_relief"
            keywords = ["paracetamol", "pain relief", "balm"]
        elif any(w in text_lower for w in ["baby", "infant", "diaper"]):
            category, intent = "baby", "baby_care"
            keywords = ["diapers", "baby formula", "baby wipes"]
        else:
            category, intent = "personal_care", "general_search"
            keywords = [w for w in text_lower.split() if len(w) > 3][:4]

        return IntentResponse(
            intent=intent,
            urgency="medium",
            category=category,
            keywords=keywords or ["supplies"],
            confidence=0.80,
        )