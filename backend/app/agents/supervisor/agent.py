import asyncio

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

        memory = (
            await self.memory_manager
            .retrieve_memory(user_id)
        )

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
                }

                for p in
                products_result
                .top_products
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

        reasoning = (
            ReasoningBuilder.build(
                intent=
                intent_result,

                urgency=
                urgency_result,

                products=
                products_result,

                sustainability=
                sustainability_result,
            )
        )

        eco = None

        if (
            sustainability_result
            .eco_alternatives
        ):
            eco = (
                sustainability_result
                .eco_alternatives[0]
                .model_dump()
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