"""Carbon savings estimation service.

Estimates carbon footprint based on product attributes (title keywords,
price range, packaging indicators) rather than just category — since all
products in the dataset share the same category.
"""

import hashlib


class CarbonService:
    """Estimates carbon footprint and savings from product attributes."""

    # Carbon impact by product attribute keywords (kg CO2e)
    KEYWORD_CARBON_IMPACT = {
        "plastic": 2.5,
        "disposable": 2.0,
        "synthetic": 1.8,
        "chemical": 1.5,
        "aerosol": 2.2,
        "organic": 0.5,
        "natural": 0.7,
        "bamboo": 0.3,
        "recycled": 0.4,
        "biodegradable": 0.3,
        "reusable": 0.2,
        "cotton": 0.6,
        "paper": 0.8,
        "glass": 1.0,
        "metal": 1.2,
        "electronic": 3.0,
        "battery": 2.8,
    }

    @classmethod
    def estimate_product_carbon(cls, product_title: str, price: float = 0.0) -> float:
        """Estimate carbon footprint of a product based on title keywords and price.

        Returns estimated kg CO2e for the product lifecycle.
        """
        title_lower = product_title.lower()
        carbon = 1.0  # Base carbon footprint

        for keyword, impact in cls.KEYWORD_CARBON_IMPACT.items():
            if keyword in title_lower:
                carbon += impact

        # Price-based heuristic: more expensive products tend to have
        # more processing/packaging
        if price > 50:
            carbon += 0.5
        elif price > 100:
            carbon += 1.0

        return round(carbon, 2)

    @classmethod
    def carbon_saved(
        cls,
        original_title: str,
        alternative_title: str,
        original_price: float = 0.0,
        alternative_price: float = 0.0,
    ) -> float:
        """Calculate carbon savings from switching to an alternative product."""
        original_carbon = cls.estimate_product_carbon(original_title, original_price)
        alt_carbon = cls.estimate_product_carbon(alternative_title, alternative_price)

        savings = max(0, round(original_carbon - alt_carbon, 2))
        return savings

    @classmethod
    def estimate(cls, category: str) -> float:
        """Legacy method — estimate by category name."""
        category_carbon = {
            "plastic": 12.0,
            "organic": 3.0,
            "recycled": 2.0,
            "local": 1.5,
            "household": 5.0,
            "food": 4.0,
            "electronics": 15.0,
        }
        return category_carbon.get(category.lower(), 5.0)
