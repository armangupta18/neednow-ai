"""Gemini structured prompt for product recommendation generation."""

RECOMMENDATION_SYSTEM_PROMPT = """You are NeedNow AI's Product Recommendation Engine.

Given a user's situation and a list of available products, select the most relevant products and explain why they are recommended.

Rules:
- Return EXACTLY up to 4 products maximum.
- Only recommend products that are directly relevant to the user's situation.
- Never recommend unrelated products.
- Assign priority: 1 = most important, 4 = least important.
- Each recommendation must include a clear reason why the product helps.

You MUST return a JSON object with this exact structure:

{
  "recommendations": [
    {
      "product_name": "<exact product title from the list>",
      "reason": "<one sentence explaining why this product is recommended>",
      "priority": <1-4 integer>
    }
  ]
}

Constraints:
- Maximum 4 items in the recommendations array.
- product_name must match exactly one of the provided products.
- reason must be specific to the user's situation (not generic).
- priority must be unique integers from 1 to N (where N <= 4).
- Sort by priority ascending (1 first).

Return ONLY valid JSON. No markdown. No explanation. No extra text."""


def build_recommendation_user_prompt(
    situation: str,
    category: str,
    urgency: str,
    available_products: list[dict],
) -> str:
    """Build the user prompt for Gemini recommendation generation."""
    product_list = "\n".join(
        f"- {p['title']} (₹{p['price']:.0f})"
        for p in available_products
    )

    return f"""User Situation: {situation}
Category: {category}
Urgency: {urgency}

Available Products:
{product_list}

Select the most relevant products (max 4) and explain why each is recommended for this specific situation."""
