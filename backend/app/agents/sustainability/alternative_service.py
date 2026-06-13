from app.agents.sustainability.scoring_service import (
    SustainabilityScoringService,
)


class AlternativeService:

    @staticmethod
    def find_best(
        original_product,
        alternatives,
    ):

        if not alternatives:
            return None

        scored = []

        for product in alternatives:

            score = (
                SustainabilityScoringService
                .calculate_score(product)
            )

            scored.append(
                (
                    product,
                    score,
                )
            )

        scored.sort(
            key=lambda x: x[1],
            reverse=True,
        )

        return scored[0][0]