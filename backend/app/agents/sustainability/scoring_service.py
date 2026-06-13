class SustainabilityScoringService:

    @staticmethod
    def calculate_score(
        product,
    ) -> float:

        score = 50.0

        category = (
            product.category.lower()
        )

        if "organic" in category:
            score += 20

        if "recycled" in category:
            score += 25

        if "local" in category:
            score += 15

        if "plastic" in category:
            score -= 20

        return min(
            100,
            max(0, score),
        )