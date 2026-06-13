from app.memory.schemas import UserMemory


class RankingService:

    @staticmethod
    def score_product(
        product,
        memory: UserMemory,
        urgency: str,
        budget: float | None,
        similarity: float,
    ) -> float:

        score = similarity * 100

        if (
            product.brand
            in memory.preferred_brands
        ):
            score += 20

        if budget:

            if product.price <= budget:
                score += 15
            else:
                score -= 15

        if urgency == "HIGH":
            score += 10

        if urgency == "CRITICAL":
            score += 20

        score += (
            memory.sustainability_score
            * 0.1
        )

        return round(score, 2)

    @staticmethod
    def rank(
        products,
        score_map,
        memory,
        urgency,
        budget,
    ):

        ranked = []

        for product in products:

            similarity = score_map.get(
                str(product.id),
                0,
            )

            score = (
                RankingService.score_product(
                    product=product,
                    memory=memory,
                    urgency=urgency,
                    budget=budget,
                    similarity=similarity,
                )
            )

            ranked.append(
                (
                    product,
                    score,
                    similarity,
                )
            )

        ranked.sort(
            key=lambda x: x[1],
            reverse=True,
        )

        return ranked