"""Sustainability score lookup service for NeedNow AI.

Provides fast in-memory lookups for pre-computed sustainability scores.
Loads scores from datasets/sustainability/sustainability_scores.json on
initialization and exposes a query API for use across the platform.

Usage:
    from app.services.sustainability_lookup import SustainabilityLookupService

    lookup = SustainabilityLookupService()
    score = lookup.get_score("product-uuid-here")
    top = lookup.get_top_sustainable(limit=10, category="Medicine")
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Response Models
# ---------------------------------------------------------------------------


class SustainabilityScoreResponse(BaseModel):
    """Sustainability score breakdown for a single product."""

    parent_asin: str
    recyclable: float = Field(ge=0, le=100)
    reusable: float = Field(ge=0, le=100)
    eco_friendly: float = Field(ge=0, le=100)
    energy_efficient: float = Field(ge=0, le=100)
    sustainable_packaging: float = Field(ge=0, le=100)
    overall_score: float = Field(ge=0, le=100)


class SustainabilityComparisonResponse(BaseModel):
    """Comparison of sustainability scores between products."""

    products: list[SustainabilityScoreResponse]
    best_product: str
    worst_product: str
    average_score: float


# ---------------------------------------------------------------------------
# Lookup Service
# ---------------------------------------------------------------------------


class SustainabilityLookupService:
    """Fast in-memory sustainability score lookup.

    Loads pre-computed scores from JSON and provides query methods
    for retrieving individual scores, top sustainable products,
    filtered lists, and comparisons.

    Args:
        scores_path: Path to the sustainability_scores.json file.
    """

    DEFAULT_PATH = "datasets/sustainability/sustainability_scores.json"

    def __init__(self, scores_path: str | Path | None = None) -> None:
        self._path = Path(scores_path or self.DEFAULT_PATH)
        self._scores: dict[str, dict[str, Any]] = {}
        self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_score(self, parent_asin: str) -> SustainabilityScoreResponse | None:
        """Look up a sustainability score by product ID.

        Args:
            parent_asin: Product identifier (UUID string).

        Returns:
            SustainabilityScoreResponse or None if not found.
        """
        data = self._scores.get(parent_asin)
        if data is None:
            return None
        return SustainabilityScoreResponse(**data)

    def get_overall_score(self, parent_asin: str) -> float:
        """Get the overall sustainability score for a product.

        Args:
            parent_asin: Product identifier.

        Returns:
            Overall score (0–100) or 0.0 if not found.
        """
        data = self._scores.get(parent_asin)
        if data is None:
            return 0.0
        return float(data.get("overall_score", 0.0))

    def get_scores_batch(self, parent_asins: list[str]) -> list[SustainabilityScoreResponse | None]:
        """Look up scores for multiple products.

        Args:
            parent_asins: List of product identifiers.

        Returns:
            List of responses (None for products not found).
        """
        return [self.get_score(asin) for asin in parent_asins]

    def get_top_sustainable(
        self,
        *,
        limit: int = 10,
        min_score: float = 0.0,
        category: str | None = None,
    ) -> list[SustainabilityScoreResponse]:
        """Get the top sustainable products.

        Args:
            limit: Maximum results.
            min_score: Minimum overall score threshold.
            category: Filter by category (requires metadata in scores).

        Returns:
            Sorted list (highest overall_score first).
        """
        filtered = [
            data for data in self._scores.values()
            if data.get("overall_score", 0) >= min_score
        ]

        if category:
            filtered = [
                data for data in filtered
                if data.get("category", "").lower() == category.lower()
            ]

        filtered.sort(key=lambda d: d.get("overall_score", 0), reverse=True)

        return [
            SustainabilityScoreResponse(**data) for data in filtered[:limit]
        ]

    def get_by_dimension(
        self,
        dimension: str,
        *,
        limit: int = 10,
        min_score: float = 50.0,
    ) -> list[SustainabilityScoreResponse]:
        """Get top products by a specific sustainability dimension.

        Args:
            dimension: One of recyclable, reusable, eco_friendly,
                energy_efficient, sustainable_packaging.
            limit: Maximum results.
            min_score: Minimum score for this dimension.

        Returns:
            Sorted list (highest dimension score first).
        """
        valid_dims = {"recyclable", "reusable", "eco_friendly", "energy_efficient", "sustainable_packaging"}
        if dimension not in valid_dims:
            logger.warning("Invalid dimension '%s'. Valid: %s", dimension, valid_dims)
            return []

        filtered = [
            data for data in self._scores.values()
            if data.get(dimension, 0) >= min_score
        ]

        filtered.sort(key=lambda d: d.get(dimension, 0), reverse=True)

        return [
            SustainabilityScoreResponse(**data) for data in filtered[:limit]
        ]

    def compare_products(
        self, parent_asins: list[str]
    ) -> SustainabilityComparisonResponse | None:
        """Compare sustainability scores across multiple products.

        Args:
            parent_asins: List of product identifiers to compare.

        Returns:
            Comparison response or None if no products found.
        """
        products: list[SustainabilityScoreResponse] = []
        for asin in parent_asins:
            score = self.get_score(asin)
            if score:
                products.append(score)

        if not products:
            return None

        best = max(products, key=lambda p: p.overall_score)
        worst = min(products, key=lambda p: p.overall_score)
        avg = sum(p.overall_score for p in products) / len(products)

        return SustainabilityComparisonResponse(
            products=products,
            best_product=best.parent_asin,
            worst_product=worst.parent_asin,
            average_score=round(avg, 2),
        )

    def count(self) -> int:
        """Return total number of scored products."""
        return len(self._scores)

    def reload(self) -> None:
        """Reload scores from disk (e.g., after regeneration)."""
        self._scores.clear()
        self._load()

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Load scores from the JSON file."""
        if not self._path.exists():
            logger.warning(
                "Sustainability scores file not found: %s. "
                "Run: python scripts/generate_sustainability_scores.py",
                self._path,
            )
            return

        try:
            with open(self._path, "r", encoding="utf-8") as f:
                self._scores = json.load(f)

            logger.info(
                "Loaded %d sustainability scores from %s",
                len(self._scores),
                self._path,
            )

        except (json.JSONDecodeError, IOError) as exc:
            logger.error("Failed to load sustainability scores: %s", exc)
