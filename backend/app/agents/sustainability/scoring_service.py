"""Sustainability scoring service.

Scores products based on title keywords indicating eco-friendliness,
since the dataset has uniform categories.
"""

import hashlib


class SustainabilityScoringService:
    """Score products for sustainability based on product attributes."""

    # Keywords that increase sustainability score
    ECO_POSITIVE = {
        "organic": 20,
        "natural": 15,
        "bamboo": 20,
        "recycled": 25,
        "biodegradable": 22,
        "reusable": 18,
        "eco": 15,
        "green": 10,
        "sustainable": 20,
        "plant-based": 18,
        "compostable": 22,
        "non-toxic": 12,
        "chemical-free": 15,
        "cruelty-free": 10,
        "vegan": 10,
        "fair trade": 12,
        "cotton": 8,
    }

    # Keywords that decrease sustainability score
    ECO_NEGATIVE = {
        "plastic": -15,
        "disposable": -12,
        "synthetic": -10,
        "chemical": -8,
        "aerosol": -12,
        "petroleum": -15,
        "pvc": -18,
        "styrofoam": -20,
        "bleach": -8,
    }

    @classmethod
    def calculate_score(cls, product) -> float:
        """Calculate sustainability score (0-100) for a product."""
        title = getattr(product, "title", "").lower()
        score = 50.0  # Neutral baseline

        for keyword, boost in cls.ECO_POSITIVE.items():
            if keyword in title:
                score += boost

        for keyword, penalty in cls.ECO_NEGATIVE.items():
            if keyword in title:
                score += penalty  # penalty is already negative

        # Deterministic variation based on product title hash (avoids all products scoring 50)
        title_hash = int(hashlib.md5(title.encode()).hexdigest()[:8], 16)
        variation = (title_hash % 20) - 10  # -10 to +10
        score += variation

        return round(min(100, max(0, score)), 1)
