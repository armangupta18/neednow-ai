"""Google Gemini LLM Service for NeedNow AI.

Supports two modes:
    - Mock mode (USE_MOCK_LLM=true): Returns realistic mock responses locally.
    - Gemini mode: Calls Google Gemini API via google-generativeai SDK.

The mock mode enables full pipeline testing without API credentials.
"""

import json
import logging
import random

import google.generativeai as genai

from app.core.settings import settings

logger = logging.getLogger(__name__)


class GeminiService:
    """LLM service with automatic mock/Gemini switching.

    Mode selection logic:
    - If GEMINI_API_KEY is set and non-empty → use Gemini (regardless of USE_MOCK_LLM)
    - If GEMINI_API_KEY is empty/missing → use mock mode
    - USE_MOCK_LLM=true forces mock mode even with a valid key (for testing)
    """

    def __init__(self) -> None:
        has_api_key = bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip())
        force_mock = settings.USE_MOCK_LLM

        # Determine mode: use Gemini if key exists AND mock not forced
        self._mock_mode = force_mock or not has_api_key
        self._model = None

        if self._mock_mode:
            if force_mock and has_api_key:
                logger.info(
                    "GeminiService: MOCK mode (forced by USE_MOCK_LLM=true, API key present)"
                )
            else:
                logger.info(
                    "GeminiService: MOCK mode (no GEMINI_API_KEY configured)"
                )
        else:
            try:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self._model = genai.GenerativeModel(
                    model_name=settings.GEMINI_MODEL_ID,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.1,
                        max_output_tokens=settings.GEMINI_MAX_TOKENS,
                    ),
                )
                logger.info(
                    "GeminiService: LIVE mode | model=%s | key=%s...%s",
                    settings.GEMINI_MODEL_ID,
                    settings.GEMINI_API_KEY[:4],
                    settings.GEMINI_API_KEY[-4:],
                )
            except Exception as exc:
                logger.warning(
                    "GeminiService: Failed to initialize (%s). Falling back to mock mode.",
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
        Logs both requests and responses for observability.
        """
        logger.info(
            "Gemini request | mode=%s | prompt_length=%d | user_prompt=%s",
            "mock" if self._mock_mode else "live",
            len(user_prompt),
            user_prompt[:100],
        )

        if self._mock_mode:
            result = self._mock_response(system_prompt, user_prompt)
        else:
            result = await self._invoke_gemini(system_prompt, user_prompt)

        logger.info(
            "Gemini response | mode=%s | response_length=%d | preview=%s",
            "mock" if self._mock_mode else "live",
            len(result),
            result[:120],
        )

        return result

    # ------------------------------------------------------------------
    # Gemini Implementation
    # ------------------------------------------------------------------

    async def _invoke_gemini(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """Call Google Gemini API (gemini-2.5-flash)."""
        try:
            logger.debug(
                "Gemini API call | model=%s | system_prompt_len=%d",
                settings.GEMINI_MODEL_ID,
                len(system_prompt),
            )

            # Gemini uses system_instruction for system prompts
            model = genai.GenerativeModel(
                model_name=settings.GEMINI_MODEL_ID,
                system_instruction=system_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=settings.GEMINI_MAX_TOKENS,
                ),
            )

            response = model.generate_content(user_prompt)

            result = response.text
            logger.info(
                "Gemini API success | model=%s | response_chars=%d",
                settings.GEMINI_MODEL_ID,
                len(result),
            )
            return result

        except Exception as exc:
            logger.error(
                "Gemini API failure | model=%s | error=%s | falling back to mock",
                settings.GEMINI_MODEL_ID,
                str(exc),
            )
            return self._mock_response(system_prompt, user_prompt)

    # ------------------------------------------------------------------
    # Mock Implementation
    # ------------------------------------------------------------------

    def _mock_response(self, system_prompt: str, user_prompt: str) -> str:
        """Generate realistic mock responses based on prompt content."""
        combined = (system_prompt + " " + user_prompt).lower()

        logger.info("Mock LLM processing: %s", user_prompt[:80])

        # Intent Agent
        if "intent" in combined and "category" in combined and "keywords" in combined:
            response = self._mock_intent(user_prompt)

        # Product Recommendation Engine
        elif "recommendation engine" in combined or "select the most relevant" in combined:
            response = self._mock_recommendation(user_prompt)

        # Urgency Agent
        elif "urgency" in combined:
            response = self._mock_urgency(user_prompt)

        # Product-related (legacy)
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
        """Generate mock intent analysis with intent label and keywords."""
        prompt_lower = user_prompt.lower()

        # Detect category and intent
        if any(w in prompt_lower for w in ["cut", "bleed", "wound", "bandage", "first aid"]):
            category = "medical"
            intent = "first_aid"
            keywords = ["bandage", "antiseptic", "gauze", "medical tape", "cotton"]
        elif any(w in prompt_lower for w in ["headache", "pain", "ache", "migraine"]):
            category = "medical"
            intent = "pain_relief"
            keywords = ["paracetamol", "ibuprofen", "pain balm", "headache relief"]
        elif any(w in prompt_lower for w in ["fever", "temperature", "hot"]):
            category = "medical"
            intent = "fever_treatment"
            keywords = ["thermometer", "paracetamol", "ORS", "ice pack"]
        elif any(w in prompt_lower for w in ["cold", "cough", "sneeze", "flu", "throat"]):
            category = "medical"
            intent = "cold_flu_relief"
            keywords = ["cough syrup", "tissues", "steam inhaler", "lozenges", "vicks"]
        elif any(w in prompt_lower for w in ["stomach", "digest", "acid", "nausea"]):
            category = "medical"
            intent = "digestive_relief"
            keywords = ["antacid", "probiotics", "electrolyte powder", "digestive tablets"]
        elif any(w in prompt_lower for w in ["skin", "rash", "itch", "allergy"]):
            category = "medical"
            intent = "skin_care"
            keywords = ["calamine lotion", "antihistamine", "moisturizer", "hydrocortisone"]
        elif any(w in prompt_lower for w in ["baby", "infant", "formula", "diaper"]):
            category = "baby"
            intent = "baby_care"
            keywords = ["baby formula", "diapers", "baby wipes", "baby powder"]
        elif any(w in prompt_lower for w in ["medicine", "insulin", "doctor"]):
            category = "medical"
            intent = "medical_supplies"
            keywords = ["prescription", "medical supplies", "first aid kit"]
        elif any(w in prompt_lower for w in ["party", "guests", "snack", "friends"]):
            category = "party"
            intent = "party_supplies"
            keywords = ["chips", "snacks", "cold drinks", "nuts", "disposable plates"]
        elif any(w in prompt_lower for w in ["clean", "soap", "detergent"]):
            category = "cleaning"
            intent = "cleaning_supplies"
            keywords = ["detergent", "soap", "disinfectant", "mop", "sponge"]
        elif any(w in prompt_lower for w in ["food", "grocery", "milk", "bread", "egg"]):
            category = "groceries"
            intent = "grocery_restock"
            keywords = ["milk", "bread", "eggs", "rice", "vegetables"]
        else:
            category = "personal_care"
            intent = "personal_care"
            keywords = ["shampoo", "toothpaste", "soap", "moisturizer"]

        # Detect urgency
        if any(w in prompt_lower for w in ["urgent", "emergency", "immediately", "now", "critical", "bleeding"]):
            urgency = "critical"
        elif any(w in prompt_lower for w in ["soon", "today", "quick", "fast", "hurry", "minutes"]):
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
            "intent": intent,
            "urgency": urgency,
            "category": category,
            "keywords": keywords,
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
    def _mock_recommendation(user_prompt: str) -> dict:
        """Generate mock Gemini-style structured recommendations."""
        # Extract product names from the Available Products list in the prompt
        lines = user_prompt.split("\n")
        available = []
        for line in lines:
            line = line.strip()
            if line.startswith("- ") and "₹" in line:
                # Extract title: "- Product Name (₹999)"
                name = line[2:].split("(₹")[0].strip()
                available.append(name)

        # Take up to 4 products
        selected = available[:4]

        recommendations = []
        reasons = [
            "Directly addresses the user's immediate need",
            "Provides essential support for the described situation",
            "Complements primary treatment for faster relief",
            "Recommended as backup for comprehensive care",
        ]

        for i, name in enumerate(selected):
            recommendations.append({
                "product_name": name,
                "reason": reasons[i] if i < len(reasons) else "Relevant to the situation",
                "priority": i + 1,
            })

        return {"recommendations": recommendations}

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
