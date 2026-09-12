import json
import logging

from pydantic import ValidationError

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

                # Ensure category and intent are valid strings
                if not data.get("category"):
                    data["category"] = "personal_care"
                if not data.get("intent"):
                    data["intent"] = "general_search"
                if not isinstance(data.get("keywords"), list):
                    raw_kw = data.get("keywords")
                    data["keywords"] = [str(k) for k in raw_kw] if isinstance(raw_kw, list) else []

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