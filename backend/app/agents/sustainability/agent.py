from app.agents.sustainability.schemas import (
    EcoAlternative,
    SustainabilityResponse,
)

from app.agents.sustainability.retrieval_service import (
    SustainabilityRetrievalService,
)

from app.agents.sustainability.carbon_service import (
    CarbonService,
)

from app.agents.sustainability.scoring_service import (
    SustainabilityScoringService,
)

from app.agents.sustainability.alternative_service import (
    AlternativeService,
)


class SustainabilityAgent:

    def __init__(
        self,
        retrieval_service:
        SustainabilityRetrievalService,
    ):
        self.retrieval_service = (
            retrieval_service
        )

    async def analyze(
        self,
        recommended_products,
    ) -> SustainabilityResponse:

        alternatives_output = []

        total_carbon_saved = 0.0

        sustainability_scores = []

        for product in recommended_products:

            # Handle both Product model (has .id) and ProductCandidate (has .product_id)
            product_id = getattr(product, 'id', None) or getattr(product, 'product_id', None)
            product_category = getattr(product, 'category', 'general')
            product_title = getattr(product, 'title', 'Product')
            product_price = getattr(product, 'price', 0.0)

            try:
                alternatives = (
                    await self.retrieval_service
                    .find_alternatives(
                        category=product_category,
                        exclude_product_id=product_id,
                    )
                )
            except Exception:
                alternatives = []

            eco_product = (
                AlternativeService.find_best(
                    product,
                    alternatives,
                )
            )

            if not eco_product:
                continue

            carbon_saved = (
                CarbonService.carbon_saved(
                    product_category,
                    eco_product.category,
                )
            )

            eco_score = (
                SustainabilityScoringService
                .calculate_score(
                    eco_product
                )
            )

            sustainability_scores.append(
                eco_score
            )

            total_carbon_saved += (
                carbon_saved
            )

            alternatives_output.append(
                EcoAlternative(
                    original_product_id=
                    product_id,

                    original_product_name=
                    product_title,

                    alternative_product_id=
                    eco_product.id,

                    alternative_product_name=
                    eco_product.title,

                    carbon_saved=
                    carbon_saved,

                    price_difference=
                    round(
                        eco_product.price
                        - product.price,
                        2,
                    ),

                    sustainability_score=
                    eco_score,
                )
            )

        overall_score = 0.0

        if sustainability_scores:

            overall_score = round(
                sum(
                    sustainability_scores
                )
                /
                len(
                    sustainability_scores
                ),
                2,
            )

        return SustainabilityResponse(
            eco_alternatives=
            alternatives_output,

            total_carbon_saved=
            round(
                total_carbon_saved,
                2,
            ),

            overall_sustainability_score=
            overall_score,
        )