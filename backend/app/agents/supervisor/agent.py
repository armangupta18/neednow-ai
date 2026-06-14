import asyncio
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
)

from app.agents.supervisor.reasoning import (
    ReasoningBuilder,
)

from app.agents.supervisor.conversation import (
    ConversationBuilder,
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
        # STEP 1
        # Intent + Urgency in parallel
        # --------------------------------

        intent_task = (
            self.intent_agent.analyze(
                situation
            )
        )

        urgency_task = (
            self.urgency_agent.analyze(
                text=situation,
                user_context=
                memory.model_dump(),
            )
        )

        intent_result, urgency_result = (
            await asyncio.gather(
                intent_task,
                urgency_task,
            )
        )

        logger.info(
            "Step 1 complete | intent=%s | category=%s | urgency=%s | keywords=%s",
            intent_result.intent,
            intent_result.category,
            urgency_result.urgency.value,
            intent_result.keywords[:5] if intent_result.keywords else [],
        )

        # --------------------------------
        # STEP 2
        # Product Recommendations
        # --------------------------------

        products_result = (
            await self.product_agent
            .recommend(
                situation=situation,
                urgency=
                urgency_result.urgency.value,

                budget=
                intent_result.budget,

                memory=memory,

                category=
                intent_result.category,
            )
        )

        logger.info(
            "Step 2 complete | products=%d | confidence=%.2f | top=%s",
            len(products_result.top_products),
            products_result.confidence,
            [p.title[:30] for p in products_result.top_products[:4]],
        )

        # --------------------------------
        # STEP 3
        # Sustainability Analysis
        # --------------------------------

        sustainability_result = (
            await self.sustainability_agent
            .analyze(
                [
                    p
                    for p in
                    products_result
                    .top_products
                ]
            )
        )

        # --------------------------------
        # STEP 4
        # Cart Builder
        # --------------------------------

        cart = {

            "category":
            intent_result.category,

            "products": [

                {
                    "id":
                    str(
                        p.product_id
                    ),

                    "title":
                    p.title,

                    "price":
                    p.price,

                    "score":
                    p.ranking_score,

                    "reason":
                    p.reason or "Matched by relevance",

                    "priority":
                    p.priority or (i + 1),
                }

                for i, p in enumerate(
                products_result
                .top_products)
            ],

            "bundles": [

                {
                    "id":
                    str(
                        p.product_id
                    ),

                    "title":
                    p.title,

                    "price":
                    p.price,
                }

                for p in
                products_result
                .bundle_products
            ],
        }

        # --------------------------------
        # STEP 5
        # Reasoning
        # --------------------------------

        reasoning = await ReasoningBuilder.build_async(
            intent=intent_result,
            urgency=urgency_result,
            products=products_result,
            sustainability=sustainability_result,
            situation=situation,
        )

        # Only show eco alternative if one genuinely exists
        eco = None
        if sustainability_result.eco_alternatives:
            # Pick the one with highest carbon savings
            best_eco = max(
                sustainability_result.eco_alternatives,
                key=lambda a: a.carbon_saved,
            )
            # Only show if there's actual carbon savings
            if best_eco.carbon_saved > 0:
                eco = best_eco.model_dump()

        # Generate conversational response (user-facing, no technical data)
        conversation_reply = await ConversationBuilder.generate_response(
            situation=situation,
            intent=intent_result,
            urgency=urgency_result,
            products=products_result,
            sustainability=sustainability_result,
        )

        logger.info(
            "Chat flow complete | user=%s | products=%d | urgency=%s | eco=%s",
            user_id,
            len(products_result.top_products),
            urgency_result.urgency.value,
            "yes" if eco else "none",
        )

        return SupervisorResponse(

            cart=cart,

            urgency={
                "level":
                urgency_result
                .urgency.value,

                "score":
                urgency_result.score,

                "explanation":
                urgency_result
                .explanation,
            },

            reasoning=reasoning,

            conversation_reply=conversation_reply,

            eco_alternative=eco,

            metadata={

                "memory_used":
                True,

                "confidence":
                products_result
                .confidence,

                "user_context":
                memory_context,
            },
        )