class ReasoningBuilder:

    @staticmethod
    def build(
        intent,
        urgency,
        products,
        sustainability=None,
    ) -> str:

        reasoning = []

        reasoning.append(
            f"Detected category '{intent.category}'."
        )

        reasoning.append(
            f"Urgency classified as "
            f"{urgency.urgency} "
            f"(score {urgency.score})."
        )

        if products.top_products:

            reasoning.append(
                f"Selected "
                f"{len(products.top_products)} "
                f"relevant products."
            )

        if sustainability:

            reasoning.append(
                f"Potential carbon saving "
                f"of "
                f"{sustainability.total_carbon_saved}kg."
            )

        return " ".join(reasoning)