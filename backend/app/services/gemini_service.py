"""Google Gemini LLM Service for NeedNow AI.

Supports two modes:
    - Mock mode (USE_MOCK_LLM=true): Returns realistic mock responses locally.
    - Gemini mode: Calls Google Gemini API via google-generativeai SDK.

The mock mode enables full pipeline testing without API credentials.
"""

import asyncio
import json
import logging
import random
import time
import uuid

import google.generativeai as genai

from app.core.settings import settings

logger = logging.getLogger(__name__)

# Per-key timeout (seconds) — value comes from `settings.GEMINI_TIMEOUT_SECONDS`
_KEY_TIMEOUT_SECONDS: int = settings.GEMINI_TIMEOUT_SECONDS

# How long (seconds) to skip a key after it fails with quota/timeout
_KEY_COOLDOWN_SECONDS: int = 60


class GeminiService:
    """LLM service with static API key counter for round-robin key rotation and mock fallback.

    Key rotation behavior:
    - Maintains a static class-level counter `_key_counter`.
    - Computes key index as `_key_counter % total_keys`.
    - Increments `_key_counter` on EVERY request attempt (both success and failure).
    - If an API key fails (e.g. 429 quota error), rotates to the next available key.
    - If all configured API keys fail, falls back gracefully to mock responses.
    """

    _key_counter: int = 0  # Static class counter across requests
    # Circuit breaker: maps key_index → Unix timestamp when it failed.
    # Key is skipped while (now - failed_at) < _KEY_COOLDOWN_SECONDS.
    _key_failures: dict[int, float] = {}

    def __init__(self) -> None:
        self._keys = settings.gemini_api_keys
        self._force_mock = settings.USE_MOCK_LLM
        self._mock_mode = self._force_mock or not self._keys
        self._model = None

        if self._mock_mode:
            if self._force_mock and self._keys:
                logger.info(
                    "GeminiService: MOCK mode (forced by USE_MOCK_LLM=true, API keys present: %d)",
                    len(self._keys),
                )
            else:
                logger.info(
                    "GeminiService: MOCK mode (no GEMINI_API_KEY configured)"
                )
        else:
            logger.info(
                "GeminiService: LIVE mode with %d API key(s) | model=%s",
                len(self._keys),
                settings.GEMINI_MODEL_ID,
            )

    @classmethod
    def get_next_key(cls, keys: list[str]) -> tuple[str, int]:
        """Get the next API key using static counter with modulo arithmetic.

        Increments `_key_counter` on every API call attempt (fail or success).

        Returns:
            Tuple of (selected_api_key, key_index)
        """
        if not keys:
            raise ValueError("No API keys available")
        idx = cls._key_counter % len(keys)
        cls._key_counter += 1
        return keys[idx], idx

    @classmethod
    def _is_key_cooling_down(cls, key_idx: int) -> bool:
        """Return True if this key index is still in its cooldown window."""
        failed_at = cls._key_failures.get(key_idx)
        if failed_at is None:
            return False
        elapsed = time.monotonic() - failed_at
        if elapsed >= _KEY_COOLDOWN_SECONDS:
            # Cooldown expired — clear it
            del cls._key_failures[key_idx]
            return False
        return True

    @classmethod
    def _mark_key_failed(cls, key_idx: int) -> None:
        """Mark a key as failed, starting its cooldown timer."""
        cls._key_failures[key_idx] = time.monotonic()

    async def invoke(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """Invoke the LLM with system and user prompts.

        Returns the text response (JSON string from the model).
        Logs both requests and responses for observability.
        """
        is_mock = self._force_mock or not self._keys

        # Short request identifier for tracing across logs
        request_id = uuid.uuid4().hex
        recv_ts = time.time()
        logger.info(
            "[REQUEST RECEIVED] id=%s ts=%s mode=%s prompt=%s",
            request_id,
            recv_ts,
            "MOCK" if is_mock else "GEMINI",
            user_prompt.replace("\n", " "),
        )

        if is_mock:
            start = time.monotonic()
            logger.info(
                "[SEND->MOCK] id=%s mode=MOCK keys=%d",
                request_id,
                len(self._keys),
            )
            result = self._mock_response(system_prompt, user_prompt)
            elapsed_ms = int((time.monotonic() - start) * 1000)
            logger.info(
                "[RECV<-MOCK] id=%s status=SUCCESS duration_ms=%d chars=%d result=%s",
                request_id,
                elapsed_ms,
                len(result),
                result.replace("\n", " "),
            )
        else:
            result = await self._invoke_gemini(system_prompt, user_prompt, request_id)

        return result

    # ------------------------------------------------------------------
    # Gemini Implementation
    # ------------------------------------------------------------------

    async def _invoke_gemini(
        self,
        system_prompt: str,
        user_prompt: str,
        request_id: str,
    ) -> str:
        """Call Google Gemini API with fallback rotation and circuit breaker.

        `request_id` is used to correlate logs for a single incoming request.
        """
        total_keys = len(self._keys)
        attempts = 0

        while attempts < total_keys:
            current_key, key_idx = self.get_next_key(self._keys)
            key_number = key_idx + 1  # 1-indexed for human-readable logs
            key_preview = f"{current_key[:4]}...{current_key[-4:]}" if len(current_key) >= 8 else "key"

            # --- Circuit breaker: skip keys still in cooldown ---
            if self._is_key_cooling_down(key_idx):
                remaining = int(
                    _KEY_COOLDOWN_SECONDS
                    - (time.monotonic() - self._key_failures[key_idx])
                )
                logger.info(
                    "[SKIP] id=%s API Key #%d of %d (%s) is cooling down — %ds remaining",
                    request_id, key_number, total_keys, key_preview, remaining,
                )
                attempts += 1
                continue

            attempts += 1

            try:
                attempt_start = time.monotonic()
                logger.info(
                    "[SEND] id=%s API Key #%d of %d (%s) | attempt=%d/%d | model=%s | timeout=%ds | prompt=%s",
                    request_id,
                    key_number,
                    total_keys,
                    key_preview,
                    attempts,
                    total_keys,
                    settings.GEMINI_MODEL_ID,
                    _KEY_TIMEOUT_SECONDS,
                    user_prompt.replace("\n", " "),
                )

                # Capture variables for the thread closure
                _key = current_key
                _sys = system_prompt
                _usr = user_prompt
                # SDK-level timeout (slightly shorter than our asyncio timeout)
                # so the SDK aborts before asyncio.wait_for fires.
                _sdk_timeout = max(5, _KEY_TIMEOUT_SECONDS - 2)

                def _call_gemini() -> str:
                    genai.configure(api_key=_key, transport="rest")
                    _model = genai.GenerativeModel(
                        model_name=settings.GEMINI_MODEL_ID,
                        system_instruction=_sys,
                        generation_config=genai.types.GenerationConfig(
                            temperature=0.1,
                            max_output_tokens=settings.GEMINI_MAX_TOKENS,
                        ),
                    )
                    return _model.generate_content(
                        _usr,
                        request_options={"timeout": _sdk_timeout},
                    ).text

                # Run blocking SDK call in thread pool with asyncio hard timeout
                result: str = await asyncio.wait_for(
                    asyncio.to_thread(_call_gemini),
                    timeout=_KEY_TIMEOUT_SECONDS,
                )

                # Success — clear any previous failure record
                self._key_failures.pop(key_idx, None)
                elapsed_ms = int((time.monotonic() - attempt_start) * 1000)

                logger.info(
                    "[RECV] id=%s API Key #%d of %d (%s) | SUCCESS | duration_ms=%d chars=%d result=%s",
                    request_id,
                    key_number,
                    total_keys,
                    key_preview,
                    elapsed_ms,
                    len(result),
                    result.replace("\n", " "),
                )
                return result

            except asyncio.TimeoutError:
                elapsed_ms = int((time.monotonic() - attempt_start) * 1000)
                self._mark_key_failed(key_idx)
                logger.warning(
                    "[TIMEOUT] id=%s API Key #%d of %d (%s) timed out after %ds (elapsed_ms=%d) — cooling down for %ds",
                    request_id, key_number, total_keys, key_preview,
                    _KEY_TIMEOUT_SECONDS, elapsed_ms, _KEY_COOLDOWN_SECONDS,
                )

            except Exception as exc:
                err_str = str(exc)
                # Detect quota errors for fast-fail circuit break
                is_quota = "429" in err_str or "quota" in err_str.lower() or "RESOURCE_EXHAUSTED" in err_str
                if is_quota:
                    self._mark_key_failed(key_idx)
                    elapsed_ms = int((time.monotonic() - attempt_start) * 1000)
                    logger.warning(
                        "[QUOTA] id=%s API Key #%d of %d (%s) — quota exceeded (elapsed_ms=%d) cooling down for %ds | error=%s",
                        request_id, key_number, total_keys, key_preview,
                        elapsed_ms, _KEY_COOLDOWN_SECONDS, err_str,
                    )
                else:
                    elapsed_ms = int((time.monotonic() - attempt_start) * 1000)
                    logger.warning(
                        "[FAIL] id=%s API Key #%d of %d (%s) | attempt=%d/%d | elapsed_ms=%d | error=%s",
                        request_id, key_number, total_keys, key_preview,
                        attempts, total_keys, elapsed_ms, err_str,
                    )

        logger.error(
            "[ALL FAILED] All %d key(s) failed/cooling — falling back to mock response",
            total_keys,
        )
        return self._mock_response(system_prompt, user_prompt)


    # ------------------------------------------------------------------
    # Mock Implementation
    # ------------------------------------------------------------------

    def _mock_response(self, system_prompt: str, user_prompt: str) -> str:
        """Generate realistic mock responses based on prompt content."""
        combined = (system_prompt + " " + user_prompt).lower()

        logger.info("Mock LLM processing: %s", user_prompt)

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
