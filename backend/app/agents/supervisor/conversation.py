"""Conversational response generator for NeedNow AI.

Generates user-friendly shopping assistant responses.
Never exposes raw JSON, urgency scores, confidence values,
or internal reasoning to the end user.
"""

import logging

from app.services.gemini_service import GeminiService

logger = logging.getLogger(__name__)

CONVERSATION_SYSTEM_PROMPT = """You are NeedNow AI, a friendly shopping assistant.

Generate a natural, conversational response to the user. You are helping them shop.

Rules:
- Write as a helpful shopping assistant, not a technical system
- NEVER show JSON, scores, urgency numbers, or technical data
- NEVER mention "intent detection", "confidence scores", or "urgency assessment"
- Use simple, warm language
- Mention specific product names and prices
- If multiple products found, highlight the top 1-2 picks
- Ask if they'd like to add to cart or see alternatives
- Keep responses to 2-4 sentences
- Use rupee symbol ₹ for prices

Return ONLY the conversational text. No JSON. No markdown formatting."""


class ConversationBuilder:
    """Generates natural language shopping responses."""

    _llm: GeminiService | None = None

    @classmethod
    def set_llm(cls, llm: GeminiService) -> None:
        cls._llm = llm

    @classmethod
    async def generate_response(
        cls,
        situation: str,
        intent,
        urgency,
        products,
        sustainability=None,
    ) -> str:
        """Generate a conversational shopping response.

        If Gemini is available, uses it for natural language generation.
        Otherwise, uses a template-based approach that still reads naturally.
        """
        # Try Gemini first
        if cls._llm and not cls._llm._mock_mode:
            try:
                return await cls._generate_with_gemini(
                    situation, intent, urgency, products, sustainability
                )
            except Exception as exc:
                logger.warning("Gemini conversation generation failed: %s", exc)

        # Fallback: template-based natural response
        return cls._build_natural_response(situation, intent, urgency, products, sustainability)

    @classmethod
    async def _generate_with_gemini(
        cls,
        situation: str,
        intent,
        urgency,
        products,
        sustainability=None,
    ) -> str:
        """Generate response using Gemini."""
        product_list = ""
        for i, p in enumerate(products.top_products[:4], 1):
            product_list += f"\n{i}. {p.title} — ₹{p.price:.0f}"

        eco_note = ""
        if sustainability and sustainability.eco_alternatives:
            alt = sustainability.eco_alternatives[0]
            eco_note = f"\nEco alternative: {alt.alternative_product_name} (saves {alt.carbon_saved}kg CO2)"

        user_prompt = f"""User said: "{situation}"

Products found:{product_list}
{eco_note}

Generate a friendly shopping response. Mention the top product by name and price. Ask if they want to add it to cart."""

        result = await cls._llm.invoke(
            system_prompt=CONVERSATION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )
        # Clean up
        result = result.strip().strip('"').strip("'").strip("`")
        if result.startswith("```"):
            result = result.split("```")[1] if "```" in result[3:] else result[3:]
        return result.strip()

    @classmethod
    def _build_natural_response(
        cls,
        situation: str,
        intent,
        urgency,
        products,
        sustainability=None,
    ) -> str:
        """Build a natural-sounding response without Gemini."""
        if not products.top_products:
            return (
                "I wasn't able to find products matching your request right now. "
                "Could you try describing what you need in a different way?"
            )

        count = len(products.top_products)
        top = products.top_products[0]
        top_title = top.title
        top_price = top.price

        # Opening varies by urgency
        urgency_level = urgency.urgency.value if hasattr(urgency.urgency, "value") else str(urgency.urgency)

        if urgency_level in ("CRITICAL", "HIGH"):
            opening = f"I understand this is urgent! I found {count} products that can help right away."
        elif count == 1:
            opening = "I found a product that matches what you're looking for."
        else:
            opening = f"I found {count} products for you."

        # Product highlight
        highlight = f" My top recommendation is **{top_title}** for ₹{top_price:.0f}."

        # Reason (if available)
        reason_text = ""
        reason = getattr(top, "reason", None)
        if reason and reason != "Matched by relevance":
            reason_text = f" {reason}."

        # Call to action
        cta = " Would you like me to add it to your cart?"

        # Eco note
        eco_text = ""
        if sustainability and sustainability.eco_alternatives:
            alt = sustainability.eco_alternatives[0]
            eco_text = f" I also found a greener alternative: {alt.alternative_product_name}."

        return opening + highlight + reason_text + eco_text + cta
