"""Reasoning builder for the supervisor response.

Generates human-readable reasoning explaining:
- Category detection
- Urgency assessment
- Product selection rationale
- Sustainability analysis (when applicable)

Uses Gemini for generating natural language when available,
falls back to structured template otherwise.
"""

import json
import logging

from app.services.gemini_service import GeminiService

logger = logging.getLogger(__name__)

REASONING_SYSTEM_PROMPT = """You are NeedNow AI's reasoning explainer. 
Generate a concise 2-3 sentence explanation of why these products were recommended.

Include:
- What situation was detected
- Why the urgency level was assigned
- Why these specific products were chosen
- Sustainability note (only if eco alternatives exist)

Write in second person ("Based on your situation..."). Be warm and helpful.
Return ONLY the reasoning text. No JSON. No markdown. No quotes."""


class ReasoningBuilder:

    _llm: GeminiService | None = None

    @classmethod
    def set_llm(cls, llm: GeminiService) -> None:
        """Inject LLM service for Gemini-powered reasoning."""
        cls._llm = llm

    @classmethod
    def build(
        cls,
        intent,
        urgency,
        products,
        sustainability=None,
    ) -> str:
        """Build reasoning text.

        Returns Gemini-generated reasoning if LLM is available and in live mode,
        otherwise falls back to structured template.
        """
        # Always generate a good structured reasoning as baseline
        reasoning = cls._build_structured(intent, urgency, products, sustainability)
        return reasoning

    @classmethod
    async def build_async(
        cls,
        intent,
        urgency,
        products,
        sustainability=None,
        situation: str = "",
    ) -> str:
        """Build reasoning using Gemini (async version).

        Falls back to structured template on failure.
        """
        if cls._llm is None or cls._llm._mock_mode:
            return cls._build_structured(intent, urgency, products, sustainability)

        try:
            product_names = [p.title for p in products.top_products[:4]]
            eco_note = ""
            if sustainability and sustainability.eco_alternatives:
                eco_note = f"An eco-friendly alternative saves {sustainability.total_carbon_saved}kg CO2."

            user_prompt = f"""Situation: {situation}
Category: {intent.category} (intent: {intent.intent})
Urgency: {urgency.urgency.value} (score: {urgency.score}/100)
Products selected: {', '.join(product_names)}
{eco_note}"""

            result = await cls._llm.invoke(
                system_prompt=REASONING_SYSTEM_PROMPT,
                user_prompt=user_prompt,
            )
            # Clean any accidental quotes/markdown
            result = result.strip().strip('"').strip("'")
            if result:
                return result
        except Exception as exc:
            logger.warning("Gemini reasoning generation failed: %s", exc)

        return cls._build_structured(intent, urgency, products, sustainability)

    @staticmethod
    def _build_structured(intent, urgency, products, sustainability=None) -> str:
        """Generate structured reasoning text from pipeline results."""
        parts = []

        # Situation understanding
        intent_label = getattr(intent, "intent", intent.category)
        parts.append(
            f"Based on your situation, I detected a '{intent_label}' need "
            f"in the {intent.category} category."
        )

        # Urgency
        urgency_level = urgency.urgency.value if hasattr(urgency.urgency, "value") else str(urgency.urgency)
        if urgency_level in ("CRITICAL", "HIGH"):
            parts.append(
                f"This is marked as {urgency_level} urgency (score {urgency.score}/100), "
                f"so I prioritized fast-acting and essential products."
            )
        else:
            parts.append(
                f"Urgency is {urgency_level} (score {urgency.score}/100)."
            )

        # Product selection
        if products.top_products:
            count = len(products.top_products)
            top_product = products.top_products[0].title
            reason = getattr(products.top_products[0], "reason", None)
            if reason:
                parts.append(f"I selected {count} products — '{top_product}' is the top pick because: {reason}")
            else:
                parts.append(f"I selected {count} products most relevant to your needs.")

        # Sustainability
        if sustainability and sustainability.eco_alternatives:
            saved = sustainability.total_carbon_saved
            if saved > 0:
                parts.append(f"A greener alternative could save {saved}kg of CO₂.")

        return " ".join(parts)
