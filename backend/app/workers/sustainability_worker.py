"""Sustainability worker for NeedNow AI.

Calculates and maintains sustainability metrics for the product catalog.
Computes eco scores, generates eco-friendly alternatives, refreshes
sustainability reports, and processes batches during off-peak periods.

Architecture:
    - SustainabilityService: Eco scoring, alternative discovery, reporting.
    - ProductRepository: Product catalog access for batch processing.

Dependencies:
    - app.services.sustainability_service.SustainabilityService
    - app.repositories.product_repository.ProductRepository
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class SustainabilityWorkerError(Exception):
    """Base exception for sustainability worker operations."""


class ScoringFailedError(SustainabilityWorkerError):
    """Raised when eco score computation fails for a product."""


class ReportRefreshError(SustainabilityWorkerError):
    """Raised when sustainability report refresh fails."""


# ---------------------------------------------------------------------------
# Result Models
# ---------------------------------------------------------------------------


@dataclass
class ScoringResult:
    """Result of scoring a single product."""

    product_id: UUID
    score: float = 0.0
    success: bool = True
    error: str | None = None


@dataclass
class AlternativesResult:
    """Result of generating alternatives for a category."""

    category: str
    alternatives_found: int = 0
    success: bool = True
    error: str | None = None


@dataclass
class CycleResult:
    """Summary of a full sustainability processing cycle."""

    status: str = "completed"
    products_scored: int = 0
    products_failed: int = 0
    reports_refreshed: int = 0
    alternatives_generated: int = 0
    categories_processed: int = 0
    duration_ms: float = 0.0
    errors: list[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None


@dataclass
class CachedScore:
    """A cached eco score with TTL."""

    product_id: UUID
    score: float
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime | None = None

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at


# ---------------------------------------------------------------------------
# Worker
# ---------------------------------------------------------------------------


class SustainabilityWorker:
    """Background worker for sustainability metric computation.

    Responsibilities:
        - Compute eco scores for new and unscored products.
        - Refresh sustainability reports periodically.
        - Generate eco-friendly alternative recommendations per category.
        - Batch process the catalog during off-peak periods.

    Designed for use with FastAPI BackgroundTasks, APScheduler, or arq.

    Args:
        sustainability_service: SustainabilityService for eco analysis.
        product_repository: ProductRepository for catalog access.
        poll_interval_seconds: Seconds between processing cycles.
        batch_size: Max products to process per cycle.
        score_cache_ttl_seconds: TTL for cached eco scores.
        max_retries: Max retries for failed scoring jobs.
    """

    def __init__(
        self,
        sustainability_service: Any,
        product_repository: Any,
        *,
        poll_interval_seconds: float = 600.0,
        batch_size: int = 100,
        score_cache_ttl_seconds: float = 3600.0,
        max_retries: int = 2,
    ) -> None:
        self.sustainability_service = sustainability_service
        self.product_repository = product_repository
        self.poll_interval_seconds = poll_interval_seconds
        self.batch_size = batch_size
        self.score_cache_ttl_seconds = score_cache_ttl_seconds
        self.max_retries = max_retries

        self._running = False
        self._task: asyncio.Task[None] | None = None
        self._score_cache: dict[UUID, CachedScore] = {}
        self._report_timestamps: dict[str, datetime] = {}
        self._total_scored = 0
        self._total_failed = 0
        self._last_cycle_result: CycleResult | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Start the background sustainability loop."""
        if self._running:
            logger.warning("SustainabilityWorker is already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(
            "SustainabilityWorker started (interval=%ds, batch=%d, cache_ttl=%ds)",
            self.poll_interval_seconds,
            self.batch_size,
            self.score_cache_ttl_seconds,
        )

    async def stop(self) -> None:
        """Gracefully stop the worker."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info(
            "SustainabilityWorker stopped (scored=%d, failed=%d, cached=%d)",
            self._total_scored,
            self._total_failed,
            len(self._score_cache),
        )

    async def run(self) -> CycleResult:
        """Execute a single full sustainability processing cycle.

        Steps:
        1. Compute eco scores for unscored products.
        2. Refresh stale sustainability reports.
        3. Generate alternatives for active categories.
        4. Cache maintenance (evict expired entries).

        Returns:
            CycleResult with detailed metrics.
        """
        start = time.perf_counter()
        result = CycleResult()

        logger.info("Sustainability cycle starting")

        try:
            # Step 1: Compute eco scores
            scoring_results = await self.compute_scores()
            result.products_scored = sum(1 for r in scoring_results if r.success)
            result.products_failed = sum(1 for r in scoring_results if not r.success)
            for r in scoring_results:
                if not r.success and r.error:
                    result.errors.append(f"product={r.product_id}: {r.error}")

            # Step 2: Refresh reports
            result.reports_refreshed = await self.refresh_reports()

            # Step 3: Generate alternatives
            alt_results = await self.generate_alternatives()
            result.alternatives_generated = sum(
                r.alternatives_found for r in alt_results if r.success
            )
            result.categories_processed = len(alt_results)

            # Step 4: Cache maintenance
            self._evict_expired_scores()

            # Finalize
            result.duration_ms = (time.perf_counter() - start) * 1000
            result.completed_at = datetime.now(timezone.utc)
            result.status = "completed" if not result.errors else "completed_with_errors"

            self._total_scored += result.products_scored
            self._total_failed += result.products_failed
            self._last_cycle_result = result

            logger.info(
                "Sustainability cycle completed: scored=%d, failed=%d, "
                "reports=%d, alternatives=%d, categories=%d (%.1fms)",
                result.products_scored,
                result.products_failed,
                result.reports_refreshed,
                result.alternatives_generated,
                result.categories_processed,
                result.duration_ms,
            )

        except Exception as exc:
            result.status = "failed"
            result.errors.append(str(exc))
            result.duration_ms = (time.perf_counter() - start) * 1000
            result.completed_at = datetime.now(timezone.utc)
            self._total_failed += 1
            logger.error("Sustainability cycle failed: %s", exc)

        return result

    # ------------------------------------------------------------------
    # Public Methods
    # ------------------------------------------------------------------

    async def compute_scores(
        self,
        product_ids: list[UUID] | None = None,
    ) -> list[ScoringResult]:
        """Compute eco scores for products.

        If no product_ids are provided, fetches unscored/stale products
        from the repository up to the configured batch_size.

        Args:
            product_ids: Optional specific product IDs to score.

        Returns:
            List of ScoringResult for each processed product.
        """
        # Determine which products to score
        if product_ids is None:
            product_ids = await self._get_unscored_product_ids()

        if not product_ids:
            logger.debug("No products to score")
            return []

        # Limit to batch size
        batch = product_ids[: self.batch_size]
        logger.info("Computing eco scores for %d products", len(batch))

        results: list[ScoringResult] = []

        for product_id in batch:
            result = await self._score_single_product(product_id)
            results.append(result)

        scored_count = sum(1 for r in results if r.success)
        logger.info(
            "Eco scoring batch complete: %d/%d succeeded", scored_count, len(batch)
        )

        return results

    async def refresh_reports(
        self,
        *,
        max_age_seconds: float | None = None,
    ) -> int:
        """Refresh stale sustainability reports.

        Re-generates reports for categories whose last report exceeds
        the max age threshold.

        Args:
            max_age_seconds: Override for report staleness threshold.
                Defaults to poll_interval_seconds * 10.

        Returns:
            Number of reports refreshed.
        """
        threshold = max_age_seconds or (self.poll_interval_seconds * 10)
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(seconds=threshold)
        refreshed = 0

        # Get active categories from repository
        categories = await self._get_active_categories()

        if not categories:
            return 0

        stale_categories: list[str] = []
        for category in categories:
            last_report = self._report_timestamps.get(category)
            if last_report is None or last_report < cutoff:
                stale_categories.append(category)

        if not stale_categories:
            logger.debug("All sustainability reports are fresh")
            return 0

        logger.info("Refreshing reports for %d stale categories", len(stale_categories))

        for category in stale_categories[: self.batch_size]:
            try:
                # Fetch products in this category
                products = await self.product_repository.search_by_category(
                    category, limit=20
                )

                if not products:
                    continue

                product_ids = [p.id for p in products]
                await self.sustainability_service.generate_report(product_ids)

                self._report_timestamps[category] = now
                refreshed += 1

                logger.debug("Refreshed sustainability report for category '%s'", category)

            except Exception as exc:
                logger.warning(
                    "Failed to refresh report for category '%s': %s", category, exc
                )

        logger.info("Refreshed %d/%d stale reports", refreshed, len(stale_categories))
        return refreshed

    async def generate_alternatives(
        self,
        categories: list[str] | None = None,
    ) -> list[AlternativesResult]:
        """Generate eco-friendly alternative recommendations per category.

        Identifies products with low sustainability scores and finds
        greener alternatives within the same category.

        Args:
            categories: Optional specific categories to process.
                If None, processes all active categories.

        Returns:
            List of AlternativesResult per processed category.
        """
        if categories is None:
            categories = await self._get_active_categories()

        if not categories:
            logger.debug("No categories to process for alternatives")
            return []

        logger.info("Generating alternatives for %d categories", len(categories))
        results: list[AlternativesResult] = []

        for category in categories[: self.batch_size]:
            result = await self._generate_category_alternatives(category)
            results.append(result)

        total_alternatives = sum(r.alternatives_found for r in results if r.success)
        logger.info(
            "Alternative generation complete: %d alternatives across %d categories",
            total_alternatives,
            len(results),
        )

        return results

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def total_scored(self) -> int:
        return self._total_scored

    @property
    def total_failed(self) -> int:
        return self._total_failed

    @property
    def cache_size(self) -> int:
        return len(self._score_cache)

    @property
    def last_cycle_result(self) -> CycleResult | None:
        return self._last_cycle_result

    # ------------------------------------------------------------------
    # Cache Access
    # ------------------------------------------------------------------

    def get_cached_score(self, product_id: UUID) -> float | None:
        """Retrieve a cached eco score if valid."""
        entry = self._score_cache.get(product_id)
        if entry is None or entry.is_expired:
            return None
        return entry.score

    def invalidate_product(self, product_id: UUID) -> bool:
        """Invalidate a cached score for a product."""
        return self._score_cache.pop(product_id, None) is not None

    def invalidate_all(self) -> int:
        """Clear the entire score cache."""
        count = len(self._score_cache)
        self._score_cache.clear()
        return count

    # ------------------------------------------------------------------
    # Private Implementation
    # ------------------------------------------------------------------

    async def _run_loop(self) -> None:
        """Internal loop executing sustainability cycles."""
        while self._running:
            try:
                await self.run()
            except Exception as exc:
                logger.error("Unexpected error in sustainability loop: %s", exc)
            await asyncio.sleep(self.poll_interval_seconds)

    async def _score_single_product(
        self,
        product_id: UUID,
        attempt: int = 1,
    ) -> ScoringResult:
        """Score a single product with retry logic."""
        result = ScoringResult(product_id=product_id)

        try:
            # Check cache first
            cached = self.get_cached_score(product_id)
            if cached is not None:
                result.score = cached
                return result

            # Compute via service
            response = await self.sustainability_service.calculate_score(product_id)
            score = response.sustainability_score

            # Cache the result
            self._cache_score(product_id, score)

            result.score = score
            logger.debug("Scored product %s: %.1f", product_id, score)

        except Exception as exc:
            if attempt < self.max_retries:
                await asyncio.sleep(0.5 * attempt)
                logger.warning(
                    "Retrying scoring for product %s (attempt %d/%d): %s",
                    product_id,
                    attempt + 1,
                    self.max_retries,
                    exc,
                )
                return await self._score_single_product(product_id, attempt + 1)

            result.success = False
            result.error = str(exc)
            logger.error(
                "Scoring failed for product %s after %d attempts: %s",
                product_id,
                attempt,
                exc,
            )

        return result

    async def _generate_category_alternatives(
        self, category: str
    ) -> AlternativesResult:
        """Generate alternatives for a single category."""
        result = AlternativesResult(category=category)

        try:
            # Fetch low-scoring products in this category
            products = await self.product_repository.search_by_category(
                category, limit=10
            )

            if not products:
                return result

            # Filter to products with low eco scores (or unscored)
            low_score_ids: list[UUID] = []
            for product in products:
                cached = self.get_cached_score(product.id)
                if cached is None or cached < 60.0:
                    low_score_ids.append(product.id)

            if not low_score_ids:
                return result

            # Generate alternatives via service
            response = await self.sustainability_service.recommend_alternatives(
                low_score_ids[:5]
            )

            result.alternatives_found = len(response.recommendations)

            logger.debug(
                "Generated %d alternatives for category '%s'",
                result.alternatives_found,
                category,
            )

        except Exception as exc:
            result.success = False
            result.error = str(exc)
            logger.warning(
                "Failed to generate alternatives for category '%s': %s",
                category,
                exc,
            )

        return result

    async def _get_unscored_product_ids(self) -> list[UUID]:
        """Get product IDs that don't have a valid cached score."""
        try:
            products = await self.product_repository.list_all(limit=self.batch_size * 2)

            unscored: list[UUID] = []
            for product in products:
                if self.get_cached_score(product.id) is None:
                    unscored.append(product.id)

            return unscored[: self.batch_size]

        except Exception as exc:
            logger.error("Failed to fetch unscored product IDs: %s", exc)
            return []

    async def _get_active_categories(self) -> list[str]:
        """Get distinct product categories from the catalog."""
        try:
            products = await self.product_repository.list_all(limit=500)
            categories = list({p.category for p in products if p.category})
            return sorted(categories)

        except Exception as exc:
            logger.error("Failed to fetch active categories: %s", exc)
            return []

    def _cache_score(self, product_id: UUID, score: float) -> None:
        """Store an eco score in the cache with TTL."""
        expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=self.score_cache_ttl_seconds
        )
        self._score_cache[product_id] = CachedScore(
            product_id=product_id,
            score=score,
            expires_at=expires_at,
        )

    def _evict_expired_scores(self) -> int:
        """Remove expired entries from the score cache."""
        expired = [
            pid for pid, entry in self._score_cache.items() if entry.is_expired
        ]
        for pid in expired:
            del self._score_cache[pid]

        if expired:
            logger.debug("Evicted %d expired score cache entries", len(expired))
        return len(expired)
