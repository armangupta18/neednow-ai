"""Bedrock LLM Service for NeedNow AI.

Supports two modes:
    - Mock mode (USE_MOCK_LLM=true): Returns realistic mock responses locally.
    - Bedrock mode: Calls Amazon Bedrock Claude API.

The mock mode enables full pipeline testing without AWS credentials.
"""

import json
import logging
import random

from app.core.settings import settings

logger = logging.getLogger(__name__)


class BedrockService:
    """LLM service with automatic mock/Bedrock switching."""

    def __init__(self) -> None:
        self._mock_mode = settings.USE_MOCK_LLM
        self._client = None

        if self._mock_mode:
            logger.info("BedrockService initialized in MOCK mode")
        else:
            try:
                import boto3
                self._client = boto3.client(
                    "bedrock-runtime",
                    region_name=settings.AWS_REGION,
                )
                logger.info("BedrockService initialized with AWS Bedrock")
            except Exception as exc:
                logger.warning(
                    "Failed to initialize Bedrock client: %s. Falling back to mock mode.",
                    exc,
                )
                self._mock_mode = True

    async def invoke(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """Invoke the LLM with system and user prompts.

        Returns the text response (JSON string from the model).
        """
        if self._mock_mode:
            return self._mock_response(system_prompt, user_prompt)

        return await self._invoke_bedrock(system_prompt, user_prompt)

    # ------------------------------------------------------------------
    # Bedrock Implementation (behind feature flag)
    # ------------------------------------------------------------------

    async def _invoke_bedrock(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """Call Amazon Bedrock Claude API."""
        try:
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": settings.BEDROCK_MAX_TOKENS,
                "temperature": 0.1,
                "system": system_prompt,
                "messages": [
                    {
                        "role": "user",
                        "content": user_prompt,
                    }
                ],
            }

            response = self._client.invoke_model(
                modelId=settings.BEDROCK_MODEL_ID,
                body=json.dumps(body),
            )

            response_body = json.loads(
                response["body"].read()
            )

            result = response_body["content"][0]["text"]
            logger.debug("Bedrock response received (%d chars)", len(result))
            return result

        except Exception as exc:
            logger.error("Bedrock invocation failed: %s. Using mock fallback.", exc)
            return self._mock_response(system_prompt, user_prompt)

    # ------------------------------------------------------------------
    # Mock Implementation
    # ------------------------------------------------------------------

    def _mock_response(self, system_prompt: str, user_prompt: str) -> str:
        """Generate realistic mock responses based on prompt content."""
        combined = (system_prompt + " " + user_prompt).lower()

        logger.info("Mock LLM processing: %s", user_prompt[:80])

        # Intent Agent
        if "intent" in combined and "category" in combined:
            response = self._mock_intent(user_prompt)

        # Urgency Agent
        elif "urgency" in combined:
            response = self._mock_urgency(user_prompt)

        # Product-related (not used directly by agents but included for completeness)
        elif "product" in combined or "recommend" in combined:
            response = self._mock_product()

        # Sustainability
        elif "sustainability" in combined or "eco" in combined:
            response = self._mock_sustainability()

        # Generic fallback
        else:
            response = self._mock_intent(user_prompt)

        result = json.dumps(response)
        logger.info("Mock LLM response generated (%d chars)", len(result))
        return result

    @staticmethod
    def _mock_intent(user_prompt: str) -> dict:
        """Generate mock intent analysis."""
        prompt_lower = user_prompt.lower()

        # Detect category from keywords
        if any(w in prompt_lower for w in ["baby", "infant", "formula", "diaper"]):
            category = "baby"
        elif any(w in prompt_lower for w in ["medicine", "fever", "pain", "insulin", "doctor"]):
            category = "medical"
        elif any(w in prompt_lower for w in ["party", "guests", "snack", "friends"]):
            category = "party"
        elif any(w in prompt_lower for w in ["clean", "soap", "detergent"]):
            category = "cleaning"
        elif any(w in prompt_lower for w in ["food", "grocery", "milk", "bread", "egg"]):
            category = "groceries"
        else:
            category = "personal_care"

        # Detect urgency
        if any(w in prompt_lower for w in ["urgent", "emergency", "immediately", "now", "critical"]):
            urgency = "critical"
        elif any(w in prompt_lower for w in ["soon", "today", "quick", "fast", "hurry"]):
            urgency = "high"
        elif any(w in prompt_lower for w in ["need", "want", "looking"]):
            urgency = "medium"
        else:
            urgency = "low"

        # Detect budget
        budget = None
        for word in prompt_lower.split():
            if word.startswith("$") or word.startswith("₹"):
                try:
                    budget = float(word[1:].replace(",", ""))
                except ValueError:
                    pass

        return {
            "category": category,
            "urgency": urgency,
            "budget": budget,
            "people_count": None,
            "confidence": round(random.uniform(0.82, 0.97), 2),
        }

    @staticmethod
    def _mock_urgency(user_prompt: str) -> dict:
        """Generate mock urgency assessment."""
        prompt_lower = user_prompt.lower()

        if any(w in prompt_lower for w in ["emergency", "critical", "life", "choking", "bleeding"]):
            urgency, score = "CRITICAL", random.randint(90, 100)
        elif any(w in prompt_lower for w in ["urgent", "immediately", "now", "hurry", "asap"]):
            urgency, score = "HIGH", random.randint(70, 89)
        elif any(w in prompt_lower for w in ["today", "soon", "need"]):
            urgency, score = "MEDIUM", random.randint(40, 69)
        else:
            urgency, score = "LOW", random.randint(10, 39)

        return {
            "urgency": urgency,
            "score": score,
            "explanation": f"Based on the situation described, urgency is assessed as {urgency}.",
        }

    @staticmethod
    def _mock_product() -> dict:
        """Generate mock product recommendations."""
        return {
            "products": [
                {"name": "Organic Health Product", "price": 499, "rating": 4.5},
                {"name": "Premium Care Item", "price": 799, "rating": 4.2},
                {"name": "Essential Daily Supply", "price": 299, "rating": 4.7},
            ]
        }

    @staticmethod
    def _mock_sustainability() -> dict:
        """Generate mock sustainability data."""
        return {
            "eco_score": random.randint(60, 95),
            "carbon_saved": f"{random.uniform(0.5, 5.0):.1f}kg",
            "recyclable": True,
            "recommendation": "Consider eco-friendly alternatives for a lower carbon footprint.",
        }
