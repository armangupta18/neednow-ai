"""Recommendation worker for NeedNow AI.

Generates personalized product recommendations in the background,
caches results for fast retrieval, and refreshes stale recommendations
for active users.

Architecture:
    - RecommendationService: Core recommendation generation logic.
    - ProductRepository: Product catalog access.
    - MemoryManager: User memory and preference context.

Dependencies:
    - app.services.recommendation_service.RecommendationService
    - app.repositories.product_repository.ProductRepository
    - app.memory.memory_manager.MemoryManager
"""

from __future__ import annotations

import asyncio
import hashlib
import json
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


class RecommendationWorkerError(Exception):
    """Base exception for recommendation worker operations."""


class GenerationFailedError(RecommendationWorkerError):
    """Raised when recommendation generation fails for a user."""


class CacheError(RecommendationWorkerError):
    """Raised when a caching operation fails."""


# ---------------------------------------------------------------------------
# Result Models
# ---------------------------------------------------------------------------


@dataclass
class RecommendationJob:
    """A single recommendation generation job."""

    user_id: UUID
    situation: str
    urgency: str = "normal"
    category: str = "general"
    budget: float | None = None
    priority: int = 0  # Higher = more urgent
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class JobResult:
    """Result of a single recommendation generation job."""

    user_id: UUID
    success: bool = True
    items_generated: int = 0
    cached: bool = False
    duration_ms: float = 0.0
    error: str | None = None


@dataclass
class CycleResult:
    """Summary of a full recommendation processing cycle."""

    status: str = "completed"
    jobs_processed: int = 0
    jobs_failed: int = 0
    recommendations_generated: int = 0
    cache_hits: int = 0
    cache_writes: int = 0
    refreshed: int = 0
    duration_ms: float = 0.0
    errors: list[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None


@dataclass
class CachedRecommendation:
    """A cached recommendation result with TTL metadata."""

    user_id: UUID
    cache_key: str
    data: dict[str, Any]
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


class RecommendationWorker:
    """Background worker for asynchronous recommendation generation.

    Responsibilities:
        - Generate personalized recommendations for queued users.
        - Cache recommendation results with configurable TTL.
        - Refresh stale recommendations for active users.
        - Precompute recommendation batches during off-peak periods.

    Designed for use with FastAPI BackgroundTasks, APScheduler, or arq.

    Args:
        recommendation_service: RecommendationService for generation logic.
        product_repository: ProductRepository for catalog access.
        memory_manager: MemoryManager for user preference context.
        poll_interval_seconds: Seconds between processing cycles.
        batch_size: Max users to process per cycle.
        cache_ttl_seconds: Seconds before cached recommendations expire.
        max_retries: Max retries for failed generation jobs.
    """

    def __init__(
        self,
        recommendation_service: Any,
        product_repository: Any,
        memory_manager: Any,
        *,
        poll_interval_seconds: float = 120.0,
        batch_size: int = 20,
        cache_ttl_seconds: float = 1800.0,
        max_retries: int = 2,
    ) -> None:
        self.recommendation_service = recommendation_service
        self.product_repository = product_repository
        self.memory_manager = memory_manager
        self.poll_interval_seconds = poll_interval_seconds
        self.batch_size = batch_size
        self.cache_ttl_seconds = cache_ttl_seconds
        self.max_retries = max_retries

        self._running = False
        self._task: asyncio.Task[None] | None = None
        self._job_queue: asyncio.PriorityQueue[tuple[int, RecommendationJob]] = (
            asyncio.PriorityQueue()
        )
        self._cache: dict[str, CachedRecommendation] = {}
        self._total_generated = 0
        self._total_failed = 0
        self._last_cycle_result: CycleResult | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Start the background recommendation loop."""
        if self._running:
            logger.warning("RecommendationWorker is already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(
            "RecommendationWorker started (interval=%ds, batch=%d, cache_ttl=%ds)",
            self.poll_interval_seconds,
            self.batch_size,
            self.cache_ttl_seconds,
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
            "RecommendationWorker stopped (generated=%d, failed=%d, cached=%d)",
            self._total_generated,
            self._total_failed,
            len(self._cache),
        )

    async def run(self) -> CycleResult:
        """Execute a single full recommendation cycle.

        Processes queued jobs, refreshes stale cached results,
        and performs cache maintenance.

        Returns:
            CycleResult with detailed metrics.
        """
        start = time.perf_counter()
        result = CycleResult()

        logger.info("Recommendation cycle starting")

        try:
            # Step 1: Process queued recommendation jobs
            job_results = await self._process_queued_jobs()
            for jr in job_results:
                if jr.success:
                    result.jobs_processed += 1
                    result.recommendations_generated += jr.items_generated
                    if jr.cached:
                        result.cache_writes += 1
                else:
                    result.jobs_failed += 1
                    if jr.error:
                        result.errors.append(f"user={jr.user_id}: {jr.error}")

            # Step 2: Refresh stale cached recommendations
            refreshed = await self.refresh_recommendations()
            result.refreshed = refreshed

            # Step 3: Cache maintenance (evict expired entries)
            self._evict_expired_cache()

            # Finalize
            result.duration_ms = (time.perf_counter() - start) * 1000
            result.completed_at = datetime.now(timezone.utc)
            result.cache_hits = self._count_valid_cache_entries()
            result.status = "completed" if not result.errors else "completed_with_errors"

            self._total_generated += result.recommendations_generated
            self._total_failed += result.jobs_failed
            self._last_cycle_result = result

            logger.info(
                "Recommendation cycle completed: processed=%d, generated=%d, "
                "refreshed=%d, cache_size=%d, failed=%d (%.1fms)",
                result.jobs_processed,
                result.recommendations_generated,
                result.refreshed,
                len(self._cache),
                result.jobs_failed,
                result.duration_ms,
            )

        except Exception as exc:
            result.status = "failed"
            result.errors.append(str(exc))
            result.duration_ms = (time.perf_counter() - start) * 1000
            result.completed_at = datetime.now(timezone.utc)
            self._total_failed += 1
            logger.error("Recommendation cycle failed: %s", exc)

        return result

    # ------------------------------------------------------------------
    # Public Methods
    # ------------------------------------------------------------------

    async def generate_recommendations(
        self,
        user_id: UUID,
        *,
        situation: str = "general browsing",
        urgency: str = "normal",
        category: str = "general",
        budget: float | None = None,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        """Generate personalized recommendations for a user.

        Checks cache first; if a valid cached result exists, returns it.
        Otherwise generates fresh recommendations via the service layer.

        Args:
            user_id: UUID of the target user.
            situation: User's current context/situation.
            urgency: Urgency level (low, normal, high, critical).
            category: Product category to focus on.
            budget: Optional budget constraint.
            use_cache: Whether to check/write cache.

        Returns:
            Dict containing recommendation data.

        Raises:
            GenerationFailedError: If recommendation generation fails.
        """
        cache_key = self._build_cache_key(user_id, situation, urgency, category)

        # Check cache
        if use_cache:
            cached = self._get_from_cache(cache_key)
            if cached is not None:
                logger.debug("Cache hit for user %s (key=%s)", user_id, cache_key[:12])
                return cached

        # Generate fresh recommendations
        try:
            from app.services.recommendation_service import RecommendationRequest

            request = RecommendationRequest(
                user_id=user_id,
                situation=situation,
                urgency=urgency,
                category=category,
                budget=budget,
            )

            response = await self.recommendation_service.recommend_products(request)
            result_data = response.model_dump()

            # Cache the result
            if use_cache:
                await self.cache_results(user_id, cache_key, result_data)

            logger.info(
                "Generated %d recommendations for user %s",
                len(response.recommended_products),
                user_id,
            )
            return result_data

        except Exception as exc:
            logger.error(
                "Recommendation generation failed for user %s: %s", user_id, exc
            )
            raise GenerationFailedError(
                f"Failed to generate recommendations for user {user_id}: {exc}"
            ) from exc

    async def refresh_recommendations(
        self,
        *,
        max_refresh: int | None = None,
    ) -> int:
        """Refresh stale cached recommendations.

        Identifies expired or near-expiry cache entries and regenerates
        them proactively to keep results fresh for active users.

        Args:
            max_refresh: Maximum entries to refresh per call.

        Returns:
            Number of entries successfully refreshed.
        """
        limit = max_refresh or self.batch_size
        refreshed = 0
        stale_entries: list[CachedRecommendation] = []

        # Find expired or soon-to-expire entries
        now = datetime.now(timezone.utc)
        refresh_threshold = now + timedelta(seconds=self.cache_ttl_seconds * 0.2)

        for entry in self._cache.values():
            if entry.expires_at and entry.expires_at <= refresh_threshold:
                stale_entries.append(entry)

        stale_entries.sort(key=lambda e: e.expires_at or now)
        stale_entries = stale_entries[:limit]

        if not stale_entries:
            return 0

        logger.info("Refreshing %d stale recommendation entries", len(stale_entries))

        for entry in stale_entries:
            try:
                # Extract generation params from cached data
                data = entry.data
                user_id = entry.user_id

                situation = data.get("_situation", "general browsing")
                urgency = data.get("_urgency", "normal")
                category = data.get("_category", "general")
                budget = data.get("_budget")

                await self.generate_recommendations(
                    user_id,
                    situation=situation,
                    urgency=urgency,
                    category=category,
                    budget=budget,
                    use_cache=True,
                )
                refreshed += 1

            except Exception as exc:
                logger.warning(
                    "Failed to refresh recommendations for user %s: %s",
                    entry.user_id,
                    exc,
                )

        logger.info("Refreshed %d/%d stale entries", refreshed, len(stale_entries))
        return refreshed

    async def cache_results(
        self,
        user_id: UUID,
        cache_key: str,
        data: dict[str, Any],
    ) -> None:
        """Cache a recommendation result with TTL.

        Args:
            user_id: UUID of the user.
            cache_key: Unique cache key for this recommendation.
            data: Recommendation data to cache.

        Raises:
            CacheError: If the caching operation fails.
        """
        try:
            expires_at = datetime.now(timezone.utc) + timedelta(
                seconds=self.cache_ttl_seconds
            )

            entry = CachedRecommendation(
                user_id=user_id,
                cache_key=cache_key,
                data=data,
                expires_at=expires_at,
            )

            self._cache[cache_key] = entry

            logger.debug(
                "Cached recommendations for user %s (key=%s, expires=%s)",
                user_id,
                cache_key[:12],
                expires_at.isoformat(),
            )

        except Exception as exc:
            logger.error("Failed to cache recommendations: %s", exc)
            raise CacheError(f"Cache write failed: {exc}") from exc

    # ------------------------------------------------------------------
    # Queue Management
    # ------------------------------------------------------------------

    async def enqueue(self, job: RecommendationJob) -> None:
        """Add a recommendation job to the priority queue."""
        # Lower priority value = higher priority in PriorityQueue
        priority = -job.priority
        await self._job_queue.put((priority, job))
        logger.debug(
            "Enqueued recommendation job for user %s (priority=%d)",
            job.user_id,
            job.priority,
        )

    async def enqueue_for_user(
        self,
        user_id: UUID,
        *,
        situation: str = "general browsing",
        urgency: str = "normal",
        category: str = "general",
        budget: float | None = None,
        priority: int = 0,
    ) -> None:
        """Convenience method to enqueue a recommendation job."""
        job = RecommendationJob(
            user_id=user_id,
            situation=situation,
            urgency=urgency,
            category=category,
            budget=budget,
            priority=priority,
        )
        await self.enqueue(job)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def total_generated(self) -> int:
        return self._total_generated

    @property
    def total_failed(self) -> int:
        return self._total_failed

    @property
    def pending_jobs(self) -> int:
        return self._job_queue.qsize()

    @property
    def cache_size(self) -> int:
        return len(self._cache)

    @property
    def last_cycle_result(self) -> CycleResult | None:
        return self._last_cycle_result

    # ------------------------------------------------------------------
    # Cache Inspection
    # ------------------------------------------------------------------

    def get_cached(self, user_id: UUID, situation: str, urgency: str, category: str) -> dict[str, Any] | None:
        """Retrieve a cached recommendation if valid."""
        cache_key = self._build_cache_key(user_id, situation, urgency, category)
        return self._get_from_cache(cache_key)

    def invalidate_user_cache(self, user_id: UUID) -> int:
        """Invalidate all cached recommendations for a user.

        Args:
            user_id: UUID of the user.

        Returns:
            Number of cache entries removed.
        """
        keys_to_remove = [
            key for key, entry in self._cache.items()
            if entry.user_id == user_id
        ]
        for key in keys_to_remove:
            del self._cache[key]

        if keys_to_remove:
            logger.info(
                "Invalidated %d cache entries for user %s",
                len(keys_to_remove),
                user_id,
            )
        return len(keys_to_remove)

    # ------------------------------------------------------------------
    # Private Implementation
    # ------------------------------------------------------------------

    async def _run_loop(self) -> None:
        """Internal loop executing recommendation cycles."""
        while self._running:
            try:
                await self.run()
            except Exception as exc:
                logger.error("Unexpected error in recommendation loop: %s", exc)
            await asyncio.sleep(self.poll_interval_seconds)

    async def _process_queued_jobs(self) -> list[JobResult]:
        """Drain and process queued recommendation jobs."""
        results: list[JobResult] = []
        processed = 0

        while not self._job_queue.empty() and processed < self.batch_size:
            try:
                _, job = self._job_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

            result = await self._process_single_job(job)
            results.append(result)
            processed += 1

        return results

    async def _process_single_job(
        self,
        job: RecommendationJob,
        attempt: int = 1,
    ) -> JobResult:
        """Process a single recommendation job with retry logic."""
        start = time.perf_counter()
        result = JobResult(user_id=job.user_id)

        try:
            data = await self.generate_recommendations(
                job.user_id,
                situation=job.situation,
                urgency=job.urgency,
                category=job.category,
                budget=job.budget,
                use_cache=True,
            )

            items = data.get("recommended_products", [])
            result.items_generated = len(items)
            result.cached = True
            result.duration_ms = (time.perf_counter() - start) * 1000

            logger.debug(
                "Job completed for user %s: %d items (%.1fms)",
                job.user_id,
                result.items_generated,
                result.duration_ms,
            )

        except Exception as exc:
            if attempt < self.max_retries:
                # Retry with backoff
                await asyncio.sleep(1.0 * attempt)
                logger.warning(
                    "Retrying recommendation job for user %s (attempt %d/%d): %s",
                    job.user_id,
                    attempt + 1,
                    self.max_retries,
                    exc,
                )
                return await self._process_single_job(job, attempt + 1)

            result.success = False
            result.error = str(exc)
            result.duration_ms = (time.perf_counter() - start) * 1000
            logger.error(
                "Recommendation job failed for user %s after %d attempts: %s",
                job.user_id,
                attempt,
                exc,
            )

        return result

    def _build_cache_key(
        self,
        user_id: UUID,
        situation: str,
        urgency: str,
        category: str,
    ) -> str:
        """Build a deterministic cache key from recommendation parameters."""
        raw = f"{user_id}:{situation}:{urgency}:{category}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    def _get_from_cache(self, cache_key: str) -> dict[str, Any] | None:
        """Retrieve a valid (non-expired) entry from cache."""
        entry = self._cache.get(cache_key)
        if entry is None:
            return None
        if entry.is_expired:
            del self._cache[cache_key]
            return None
        return entry.data

    def _evict_expired_cache(self) -> int:
        """Remove all expired entries from the cache."""
        expired_keys = [
            key for key, entry in self._cache.items() if entry.is_expired
        ]
        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            logger.debug("Evicted %d expired cache entries", len(expired_keys))
        return len(expired_keys)

    def _count_valid_cache_entries(self) -> int:
        """Count non-expired cache entries."""
        return sum(1 for entry in self._cache.values() if not entry.is_expired)
