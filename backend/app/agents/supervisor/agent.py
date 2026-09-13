import logging

from app.memory.memory_manager import (
    MemoryManager,
)

from app.memory.memory_context_builder import (
    MemoryContextBuilder,
)

from app.agents.intent.agent import (
    IntentAgent,
)

from app.agents.urgency.agent import (
    UrgencyAgent,
)

from app.agents.product.agent import (
    ProductAgent,
)

from app.agents.sustainability.agent import (
    SustainabilityAgent,
)

from app.agents.supervisor.schemas import (
    SupervisorResponse,
    ProductReasoning,
)

from app.agents.supervisor.synthesis import (
    SynthesisBuilder,
)


class SupervisorAgent:

    def __init__(
        self,
        intent_agent: IntentAgent,
        urgency_agent: UrgencyAgent,
        product_agent: ProductAgent,
        sustainability_agent: SustainabilityAgent,
        memory_manager: MemoryManager,
    ):

        self.intent_agent = intent_agent

        self.urgency_agent = urgency_agent

        self.product_agent = product_agent

        self.sustainability_agent = (
            sustainability_agent
        )

        self.memory_manager = (
            memory_manager
        )

    async def execute(
        self,
        user_id,
        situation: str,
    ) -> SupervisorResponse:

        logger = logging.getLogger("supervisor")
        logger.info(
            "Chat flow started | user=%s | message=%s",
            user_id,
            situation[:100],
        )

        try:
            memory = (
                await self.memory_manager
                .retrieve_memory(user_id)
            )
        except Exception:
            # User not found or memory retrieval failed
            # Continue with empty/default memory
            from app.memory.schemas import UserMemory
            memory = UserMemory()

        memory_context = (
            MemoryContextBuilder.build(
                memory
            )
        )

        # --------------------------------
        # STEP 1 — Intent Detection
        # --------------------------------

        intent_result = await self.intent_agent.analyze(situation)

        logger.info(
            "Step 1 complete | intent=%s | category=%s | keywords=%s",
            intent_result.intent,
            intent_result.category,
            intent_result.keywords[:5] if intent_result.keywords else [],
        )

        # --------------------------------
        # STEP 2 — Product Recommendations
        # --------------------------------

        products_result = await self.product_agent.recommend(
            situation=situation,
            urgency="STANDARD",      # Neutral urgency when agent is disabled
            budget=intent_result.budget,
            memory=memory,
            category=intent_result.category,
        )

        logger.info(
            "Step 2 complete | products=%d | confidence=%.2f | top=%s",
            len(products_result.top_products),
            products_result.confidence,
            [p.title[:30] for p in products_result.top_products[:4]],
        )

        # --------------------------------
        # STEP 3 — Build Cart (all products)
        # --------------------------------

        cart = {
            "category": intent_result.category,
            "products": [
                {
                    "id": str(p.product_id),
                    "title": p.title,
                    "price": p.price,
                    "score": p.ranking_score,
                    "reason": p.reason or "Matched by relevance",
                    "priority": p.priority or (i + 1),
                }
                for i, p in enumerate(products_result.top_products)
            ],
            "bundles": [
                {
                    "id": str(p.product_id),
                    "title": p.title,
                    "price": p.price,
                }
                for p in products_result.bundle_products
            ],
        }

        # --------------------------------
        # STEP 4 — Combined Synthesis
        # Single Gemini call → conversation + per-product reasoning
        # --------------------------------

        conversation_reply, raw_reasoning = await SynthesisBuilder.build(
            situation=situation,
            category=intent_result.category,
            top_products=products_result.top_products[:4],
        )

        product_reasonings = [
            ProductReasoning(
                product_name=item.get("product_name", ""),
                reason=item.get("reason", ""),
            )
            for item in raw_reasoning
            if item.get("product_name") and item.get("reason")
        ]

        # Build legacy reasoning string for backward compat
        reasoning_lines = [
            f"{i+1}. **{r.product_name}**: {r.reason}"
            for i, r in enumerate(product_reasonings)
        ]
        reasoning_str = "\n".join(reasoning_lines) if reasoning_lines else "Recommendations based on your situation and search context."

        logger.info(
            "Chat flow complete | user=%s | products=%d | reasoning_items=%d",
            user_id,
            len(products_result.top_products),
            len(product_reasonings),
        )

        return SupervisorResponse(
            cart=cart,
            urgency=None,
            reasoning=reasoning_str,
            product_reasonings=product_reasonings,
            conversation_reply=conversation_reply,
            eco_alternative=None,
            metadata={
                "memory_used": True,
                "confidence": products_result.confidence,
                "user_context": memory_context,
            },
        )