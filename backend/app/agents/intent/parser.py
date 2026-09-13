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
    def _coerce_text(value) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            cleaned = value.strip()
            return cleaned or None
        cleaned = str(value).strip()
        return cleaned or None

    @staticmethod
    def _coerce_number(value):
        if value is None:
            return None
        if isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return value
        if isinstance(value, str):
            cleaned = value.strip()
            if not cleaned:
                return None
            try:
                return float(cleaned) if "." in cleaned else int(cleaned)
            except ValueError:
                return None
        return None

    @staticmethod
    def _coerce_list(value) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            cleaned = value.strip()
            if not cleaned:
                return []
            if "," in cleaned:
                return [part.strip() for part in cleaned.split(",") if part.strip()]
            return [cleaned]
        return [str(value).strip()] if str(value).strip() else []

    @staticmethod
    def parse(
        response_text: str,
        user_prompt: str = "",
    ) -> IntentResponse:
        """Parse raw response from Gemini into a validated IntentResponse."""
        data = HelperUtils.extract_json(response_text)

        if isinstance(data, dict):
            try:
                # Sanitize urgency literal
                urgency = str(data.get("urgency", "medium")).lower().strip()
                if urgency not in ("low", "medium", "high", "critical"):
                    urgency = "medium"
                data["urgency"] = urgency

                # Sanitize confidence range
                try:
                    conf = float(data.get("confidence", 0.85))
                except (ValueError, TypeError):
                    conf = 0.85
                data["confidence"] = max(0.0, min(1.0, conf))

                # Normalize optional scalar fields
                data["budget"] = IntentParser._coerce_number(data.get("budget"))
                data["people_count"] = IntentParser._coerce_number(data.get("people_count"))
                data["gender"] = IntentParser._coerce_text(data.get("gender"))
                data["age"] = IntentParser._coerce_text(data.get("age"))
                data["other_request"] = IntentParser._coerce_text(data.get("other_request"))
                data["special_request"] = IntentParser._coerce_text(data.get("special_request"))

                # Ensure category and intent are valid strings
                if not data.get("category"):
                    data["category"] = "personal_care"
                if not data.get("intent"):
                    data["intent"] = "general_search"
                if not isinstance(data.get("keywords"), list):
                    raw_kw = data.get("keywords")
                    data["keywords"] = [str(k) for k in raw_kw] if isinstance(raw_kw, list) else []
                data["dietry_restrictions"] = IntentParser._coerce_list(
                    data.get("dietry_restrictions")
                )
                data["dietry_preferences"] = IntentParser._coerce_list(
                    data.get("dietry_preferences")
                )

                return IntentResponse(**data)
            except Exception as val_exc:
                logger.warning("Intent validation warning: %s. Falling back to heuristic analysis.", val_exc)

        # Fallback if LLM response could not be parsed into dict
        logger.warning(
            "Intent parsing fallback triggered for response length=%d",
            len(response_text) if response_text else 0,
        )
        return IntentParser._fallback_intent(response_text + " " + user_prompt)

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