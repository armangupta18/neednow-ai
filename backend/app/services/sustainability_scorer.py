"""Sustainability scoring service for NeedNow AI.

Generates and manages sustainability scores for products based on
keyword analysis of title, description, features, and categories.

Scores products across five dimensions:
    - recyclable
    - reusable
    - eco_friendly
    - energy_efficient
    - sustainable_packaging

Stores/loads scores from: datasets/sustainability/sustainability_scores.json
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Score Model
# ---------------------------------------------------------------------------


@dataclass
class SustainabilityScore:
    """Sustainability score breakdown for a product."""

    parent_asin: str
    recyclable: float = 0.0
    reusable: float = 0.0
    eco_friendly: float = 0.0
    energy_efficient: float = 0.0
    sustainable_packaging: float = 0.0

    @property
    def overall_score(self) -> float:
        """Weighted average of all dimensions (0–100)."""
        return round(
            (
                self.recyclable * 0.20
                + self.reusable * 0.20
                + self.eco_friendly * 0.25
                + self.energy_efficient * 0.15
                + self.sustainable_packaging * 0.20
            ),
            2,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "parent_asin": self.parent_asin,
            "recyclable": self.recyclable,
            "reusable": self.reusable,
            "eco_friendly": self.eco_friendly,
            "energy_efficient": self.energy_efficient,
            "sustainable_packaging": self.sustainable_packaging,
            "overall_score": self.overall_score,
        }


# ---------------------------------------------------------------------------
# Keyword Definitions (drives scoring heuristics)
# ---------------------------------------------------------------------------

_RECYCLABLE_KEYWORDS = [
    "recyclable", "recycled", "recycle", "post-consumer",
    "biodegradable", "compostable", "decomposable",
]

_REUSABLE_KEYWORDS = [
    "reusable", "refillable", "washable", "multi-use",
    "rechargeable", "durable", "long-lasting", "lifetime",
]

_ECO_FRIENDLY_KEYWORDS = [
    "eco-friendly", "eco friendly", "organic", "natural",
    "plant-based", "vegan", "cruelty-free", "non-toxic",
    "chemical-free", "paraben-free", "sulfate-free",
    "green", "sustainable", "earth-friendly", "bio",
]

_ENERGY_EFFICIENT_KEYWORDS = [
    "energy-efficient", "energy efficient", "energy star",
    "low-power", "solar", "led", "energy saving",
    "low energy", "eco mode", "auto-off",
]

_SUSTAINABLE_PACKAGING_KEYWORDS = [
    "sustainable packaging", "eco packaging", "minimal packaging",
    "plastic-free", "paper packaging", "cardboard", "bamboo",
    "zero waste", "compostable packaging", "recyclable packaging",
    "no plastic", "reduced packaging",
]


# ---------------------------------------------------------------------------
# Sustainability Scorer Service
# ---------------------------------------------------------------------------


class SustainabilityScorerService:
    """Generates and manages sustainability scores for products.

    Analyzes product text (title, description, features, categories)
    for sustainability keywords and produces dimension-level scores.

    Args:
        scores_path: Path to the JSON file for persistence.
    """

    DEFAULT_SCORES_PATH = "datasets/sustainability/sustainability_scores.json"

    def __init__(self, scores_path: str | Path | None = None) -> None:
        self._scores_path = Path(scores_path or self.DEFAULT_SCORES_PATH)
        self._scores: dict[str, SustainabilityScore] = {}

        # Load existing scores if available
        self._load_scores()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def score_product(self, product: dict[str, Any]) -> SustainabilityScore:
        """Generate a sustainability score for a single product.

        Analyzes title, description, features, and categories for
        sustainability keywords across all five dimensions.

        Args:
            product: Dict with product fields (title, description,
                features, categories, parent_asin).

        Returns:
            SustainabilityScore with dimension-level scores.
        """
        parent_asin = str(product.get("parent_asin", product.get("id", "")))
        text = self._build_text(product).lower()

        score = SustainabilityScore(
            parent_asin=parent_asin,
            recyclable=self._calculate_dimension_score(text, _RECYCLABLE_KEYWORDS),
            reusable=self._calculate_dimension_score(text, _REUSABLE_KEYWORDS),
            eco_friendly=self._calculate_dimension_score(text, _ECO_FRIENDLY_KEYWORDS),
            energy_efficient=self._calculate_dimension_score(text, _ENERGY_EFFICIENT_KEYWORDS),
            sustainable_packaging=self._calculate_dimension_score(text, _SUSTAINABLE_PACKAGING_KEYWORDS),
        )

        # Cache the score
        self._scores[parent_asin] = score
        return score

    def score_products(
        self, products: list[dict[str, Any]]
    ) -> list[SustainabilityScore]:
        """Score a batch of products.

        Args:
            products: List of product dicts.

        Returns:
            List of SustainabilityScore objects.
        """
        results: list[SustainabilityScore] = []
        for product in products:
            try:
                score = self.score_product(product)
                results.append(score)
            except Exception as exc:
                logger.warning(
                    "Failed to score product %s: %s",
                    product.get("parent_asin", "unknown"),
                    exc,
                )
        return results

    def get_score(self, parent_asin: str) -> SustainabilityScore | None:
        """Look up a cached sustainability score by parent_asin.

        Args:
            parent_asin: Product identifier.

        Returns:
            SustainabilityScore or None if not scored.
        """
        return self._scores.get(parent_asin)

    def get_overall_score(self, parent_asin: str) -> float:
        """Get the overall sustainability score for a product.

        Args:
            parent_asin: Product identifier.

        Returns:
            Overall score (0–100) or 0.0 if not found.
        """
        score = self._scores.get(parent_asin)
        return score.overall_score if score else 0.0

    def get_all_scores(self) -> dict[str, SustainabilityScore]:
        """Return all cached scores."""
        return dict(self._scores)

    def get_top_sustainable(
        self, *, limit: int = 10, min_score: float = 0.0
    ) -> list[SustainabilityScore]:
        """Get the top-rated sustainable products.

        Args:
            limit: Maximum results.
            min_score: Minimum overall score threshold.

        Returns:
            Sorted list of SustainabilityScore (highest first).
        """
        filtered = [
            s for s in self._scores.values() if s.overall_score >= min_score
        ]
        filtered.sort(key=lambda s: s.overall_score, reverse=True)
        return filtered[:limit]

    def save_scores(self) -> None:
        """Persist all scores to the JSON file."""
        self._scores_path.parent.mkdir(parents=True, exist_ok=True)

        data = {asin: score.to_dict() for asin, score in self._scores.items()}

        with open(self._scores_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(
            "Saved %d sustainability scores to %s",
            len(data),
            self._scores_path,
        )

    def count(self) -> int:
        """Return the number of scored products."""
        return len(self._scores)

    # ------------------------------------------------------------------
    # Private Helpers
    # ------------------------------------------------------------------

    def _load_scores(self) -> None:
        """Load scores from the JSON file if it exists."""
        if not self._scores_path.exists():
            logger.debug("No existing scores file: %s", self._scores_path)
            return

        try:
            with open(self._scores_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for asin, score_data in data.items():
                self._scores[asin] = SustainabilityScore(
                    parent_asin=score_data.get("parent_asin", asin),
                    recyclable=score_data.get("recyclable", 0.0),
                    reusable=score_data.get("reusable", 0.0),
                    eco_friendly=score_data.get("eco_friendly", 0.0),
                    energy_efficient=score_data.get("energy_efficient", 0.0),
                    sustainable_packaging=score_data.get("sustainable_packaging", 0.0),
                )

            logger.info(
                "Loaded %d sustainability scores from %s",
                len(self._scores),
                self._scores_path,
            )

        except (json.JSONDecodeError, IOError) as exc:
            logger.warning("Failed to load scores file: %s", exc)

    @staticmethod
    def _calculate_dimension_score(text: str, keywords: list[str]) -> float:
        """Calculate a 0–100 score based on keyword presence and density.

        Scoring logic:
            - Each keyword hit adds points.
            - Multiple distinct keywords are rewarded more.
            - Capped at 100.

        Args:
            text: Lowercased product text.
            keywords: List of keywords for this dimension.

        Returns:
            Score between 0.0 and 100.0.
        """
        if not text:
            return 0.0

        hits = 0
        unique_hits = 0

        for keyword in keywords:
            count = text.count(keyword)
            if count > 0:
                unique_hits += 1
                hits += count

        if unique_hits == 0:
            return 0.0

        # Base score from unique keyword coverage
        coverage = unique_hits / len(keywords)
        base_score = coverage * 70.0

        # Bonus for multiple occurrences (capped)
        density_bonus = min(hits * 5.0, 30.0)

        return min(100.0, round(base_score + density_bonus, 2))

    @staticmethod
    def _build_text(product: dict[str, Any]) -> str:
        """Combine product fields into a single text for analysis."""
        parts: list[str] = []

        title = product.get("title", "")
        if isinstance(title, str) and title:
            parts.append(title)

        description = product.get("description", "")
        if isinstance(description, list):
            parts.append(" ".join(str(d) for d in description if d))
        elif isinstance(description, str) and description:
            parts.append(description)

        features = product.get("features", [])
        if isinstance(features, list):
            parts.append(" ".join(str(f) for f in features if f))

        categories = product.get("categories", [])
        if isinstance(categories, list):
            for cat in categories:
                if isinstance(cat, list):
                    parts.append(" ".join(str(c) for c in cat if c))
                elif isinstance(cat, str):
                    parts.append(cat)

        return " ".join(parts)
