class CarbonService:

    CATEGORY_CARBON = {

        "plastic": 12.0,
        "organic": 3.0,
        "recycled": 2.0,
        "local": 1.5,
        "household": 5.0,
        "food": 4.0,
        "electronics": 15.0,
    }

    @classmethod
    def estimate(
        cls,
        category: str,
    ) -> float:

        return cls.CATEGORY_CARBON.get(
            category.lower(),
            5.0,
        )

    @classmethod
    def carbon_saved(
        cls,
        original_category: str,
        eco_category: str,
    ) -> float:

        original = cls.estimate(
            original_category
        )

        eco = cls.estimate(
            eco_category
        )

        return max(
            0,
            round(original - eco, 2),
        )