"""Synthesis builder — combines Reasoning and Conversation into a single Gemini call.

Returns a structured JSON with:
  - "conversation": Friendly shopping assistant reply (shown in chat bubble).
  - "reasoning": Array of per-product reasoning items (shown in reasoning panel).

Replaces the separate ReasoningBuilder + ConversationBuilder calls with a single
combined LLM request, cutting latency and ensuring perfect consistency between
what the assistant says and why.
"""

import json
import logging

from app.services.gemini_service import GeminiService

logger = logging.getLogger(__name__)

SYNTHESIS_SYSTEM_PROMPT = """You are NeedNow AI — a friendly, smart shopping assistant.

Your job is to generate TWO things simultaneously in a single JSON response:

1. "conversation": A warm, natural shopping reply (2-4 sentences). Mention top 1-2 product names with ₹ prices. Ask if the user wants to add to cart. NEVER show technical data, urgency scores, or internal labels.

2. "reasoning": An array of reasoning objects — one per recommended product (max 4). Each object explains specifically why that product helps in this situation.

You MUST return ONLY this JSON structure:
{
  "conversation": "<friendly shopping assistant reply>",
  "reasoning": [
    {"product_name": "<exact product name>", "reason": "<one sentence why this product helps>"},
    {"product_name": "<exact product name>", "reason": "<one sentence why this product helps>"}
  ]
}

Rules:
- conversation: Use ₹ for prices. Be warm and helpful. 2-4 sentences max.
- reasoning: Only include products that were actually recommended (max 4).
- reason: Must be specific to the user's situation — not generic.
- product_name: Must match exactly from the provided product list.
- Return ONLY valid JSON. No markdown. No extra text. No explanations outside the JSON."""


class SynthesisBuilder:
    """Generates combined conversation + reasoning in a single Gemini call."""

    _llm: GeminiService | None = None

    @classmethod
    def set_llm(cls, llm: GeminiService) -> None:
        cls._llm = llm

    @classmethod
    async def build(
        cls,
        situation: str,
        category: str,
        top_products: list,  # List of ProductCandidate (top 4)
    ) -> tuple[str, list[dict]]:
        """Generate conversation reply and per-product reasoning in one Gemini call.

        Returns:
            Tuple of (conversation_text, reasoning_list)
            reasoning_list is a list of {"product_name": str, "reason": str}
        """
        if cls._llm is None or cls._llm._mock_mode:
            return cls._build_fallback(situation, top_products)

        # Build the user prompt
        product_lines = ""
        for i, p in enumerate(top_products[:4], 1):
            product_lines += f"\n{i}. {p.title} — ₹{p.price:.0f}"

        user_prompt = f"""User situation: "{situation}"
Category: {category}

Recommended products:{product_lines}

Generate the conversation reply and reasoning for each product."""

        try:
            raw = await cls._llm.invoke(
                system_prompt=SYNTHESIS_SYSTEM_PROMPT,
                user_prompt=user_prompt,
            )

            # Extract JSON from response
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1] if "```" in raw[3:] else raw[3:]
                raw = raw.strip()

            data = json.loads(raw)
            conversation = str(data.get("conversation", "")).strip().strip('"').strip("'")
            reasoning = data.get("reasoning", [])

            if not isinstance(reasoning, list):
                reasoning = []

            if conversation:
                return conversation, reasoning

        except Exception as exc:
            logger.warning("SynthesisBuilder Gemini call failed: %s", exc)

        return cls._build_fallback(situation, top_products)

    @staticmethod
    def _build_fallback(situation: str, top_products: list) -> tuple[str, list[dict]]:
        """Template-based fallback when Gemini is unavailable."""
        if not top_products:
            return (
                "I wasn't able to find products matching your request right now. "
                "Could you try describing what you need differently?",
                [],
            )

        count = len(top_products[:4])
        top = top_products[0]

        if count == 1:
            conversation = (
                f"I found a great match for your situation! "
                f"My top recommendation is **{top.title}** for ₹{top.price:.0f}. "
                f"Would you like me to add it to your cart?"
            )
        else:
            conversation = (
                f"I found {count} products for you! "
                f"My top recommendation is **{top.title}** for ₹{top.price:.0f}. "
                f"Would you like to add it to your cart?"
            )

        reasoning = []
        for p in top_products[:4]:
            reason = p.reason if p.reason and p.reason != "Also relevant to your search" else "Highly relevant to your situation based on your description."
            reasoning.append({
                "product_name": p.title,
                "reason": reason,
            })

        return conversation, reasoning
