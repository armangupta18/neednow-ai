"""Memory sync worker for NeedNow AI.

Synchronizes Memory Engine data with persistent storage and FAISS vector
indexes. Handles short-term to long-term memory promotion, stale memory
cleanup, and embedding index updates.

Architecture:
    - MemoryManager: Provides memory state access and decay logic.
    - MemoryRepository: Persistent JSONB storage on the User model.
    - VectorSync: FAISS index synchronization for semantic retrieval.

Dependencies:
    - app.memory.memory_manager.MemoryManager
    - app.repositories.memory_repository.MemoryRepository
    - app.vectorstore.sync.VectorSync
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


class MemorySyncError(Exception):
    """Base exception for memory sync operations."""


class MemorySyncTimeoutError(MemorySyncError):
    """Raised when a sync operation exceeds its deadline."""


# ---------------------------------------------------------------------------
# Result Models
# ---------------------------------------------------------------------------


@dataclass
class SyncCycleResult:
    """Summary of a single sync cycle."""

    status: str = "completed"
    users_synced: int = 0
    short_term_flushed: int = 0
    long_term_updated: int = 0
    stale_cleaned: int = 0
    embeddings_triggered: int = 0
    duration_ms: float = 0.0
    errors: list[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None


@dataclass
class UserSyncResult:
    """Result of syncing a single user's memory."""

    user_id: UUID
    short_term_flushed: bool = False
    long_term_updated: bool = False
    embedding_triggered: bool = False
    error: str | None = None


# ---------------------------------------------------------------------------
# Worker
# ---------------------------------------------------------------------------


class MemorySyncWorker:
    """Background worker that synchronizes memory state across storage layers.

    Responsibilities:
        - Sync short-term memory: flush expired session data to long-term.
        - Sync long-term memory: persist updated preferences and patterns.
        - Detect stale memories: identify and clean expired entries.
        - Trigger embedding updates: notify VectorSync when content changes.
        - Batch synchronization: process multiple users per cycle.

    Designed for use with FastAPI BackgroundTasks, APScheduler, or arq.

    Args:
        memory_manager: MemoryManager instance for memory state access.
        memory_repository: MemoryRepository for persistent storage.
        vector_sync: VectorSync for embedding index updates (optional).
        sync_interval_seconds: Seconds between sync cycles.
        batch_size: Max users to process per cycle.
        stale_threshold_hours: Hours after which short-term memory is stale.
        max_retries: Retries per user on transient failure.
    """

    def __init__(
        self,
        memory_manager: Any,
        memory_repository: Any,
        vector_sync: Any | None = None,
        *,
        sync_interval_seconds: float = 300.0,
        batch_size: int = 50,
        stale_threshold_hours: float = 1.0,
        max_retries: int = 2,
    ) -> None:
        self.memory_manager = memory_manager
        self.memory_repository = memory_repository
        self.vector_sync = vector_sync
        self.sync_interval_seconds = sync_interval_seconds
        self.batch_size = batch_size
        self.stale_threshold_hours = stale_threshold_hours
        self.max_retries = max_retries

        self._running = False
        self._task: asyncio.Task[None] | None = None
        self._total_synced = 0
        self._total_errors = 0
        self._last_cycle_result: SyncCycleResult | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Start the background sync loop."""
        if self._running:
            logger.warning("MemorySyncWorker is already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(
            "MemorySyncWorker started (interval=%ds, batch_size=%d, stale_threshold=%dh)",
            self.sync_interval_seconds,
            self.batch_size,
            self.stale_threshold_hours,
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
            "MemorySyncWorker stopped (total_synced=%d, total_errors=%d)",
            self._total_synced,
            self._total_errors,
        )

    async def run(self) -> SyncCycleResult:
        """Execute a single full sync cycle.

        Orchestrates the complete memory synchronization workflow:
        1. Detect users with pending memory changes.
        2. Sync short-term memory (flush expired sessions).
        3. Sync long-term memory (persist updates).
        4. Cleanup stale memories.
        5. Trigger embedding updates for changed content.

        Returns:
            SyncCycleResult with detailed metrics.
        """
        start = time.perf_counter()
        result = SyncCycleResult()

        logger.info("Memory sync cycle starting")

        try:
            # Step 1: Get users with active memory
            user_ids = await self._get_active_user_ids()
            logger.debug("Found %d users with active memory", len(user_ids))

            # Step 2 & 3: Sync each user's memory
            user_results = await self.sync_memories(user_ids)

            for ur in user_results:
                if ur.error:
                    result.errors.append(f"user={ur.user_id}: {ur.error}")
                else:
                    result.users_synced += 1
                if ur.short_term_flushed:
                    result.short_term_flushed += 1
                if ur.long_term_updated:
                    result.long_term_updated += 1
                if ur.embedding_triggered:
                    result.embeddings_triggered += 1

            # Step 4: Cleanup stale memories
            result.stale_cleaned = await self.cleanup_stale_memories()

            # Finalize
            result.duration_ms = (time.perf_counter() - start) * 1000
            result.completed_at = datetime.now(timezone.utc)
            result.status = "completed" if not result.errors else "completed_with_errors"

            self._total_synced += result.users_synced
            self._total_errors += len(result.errors)
            self._last_cycle_result = result

            logger.info(
                "Memory sync cycle completed: users=%d, flushed=%d, updated=%d, "
                "stale_cleaned=%d, embeddings=%d, errors=%d (%.1fms)",
                result.users_synced,
                result.short_term_flushed,
                result.long_term_updated,
                result.stale_cleaned,
                result.embeddings_triggered,
                len(result.errors),
                result.duration_ms,
            )

        except Exception as exc:
            result.status = "failed"
            result.errors.append(str(exc))
            result.duration_ms = (time.perf_counter() - start) * 1000
            result.completed_at = datetime.now(timezone.utc)
            self._total_errors += 1
            logger.error("Memory sync cycle failed: %s", exc)

        return result

    # ------------------------------------------------------------------
    # Public Sync Methods
    # ------------------------------------------------------------------

    async def sync_memories(
        self,
        user_ids: list[UUID],
    ) -> list[UserSyncResult]:
        """Batch synchronize memory for multiple users.

        Processes users in batches up to the configured batch_size.
        Each user's memory is synced independently so a single failure
        does not block others.

        Args:
            user_ids: List of user UUIDs to sync.

        Returns:
            List of UserSyncResult for each processed user.
        """
        results: list[UserSyncResult] = []

        for batch_start in range(0, len(user_ids), self.batch_size):
            batch = user_ids[batch_start : batch_start + self.batch_size]

            batch_results = await asyncio.gather(
                *[self.sync_user_memory(uid) for uid in batch],
                return_exceptions=False,
            )
            results.extend(batch_results)

        logger.debug("Synced %d users total", len(results))
        return results

    async def sync_user_memory(
        self,
        user_id: UUID,
    ) -> UserSyncResult:
        """Synchronize a single user's memory state.

        Performs:
        1. Retrieve current memory state from MemoryManager.
        2. Flush expired short-term memory to long-term storage.
        3. Persist long-term memory updates to the repository.
        4. Trigger embedding re-generation if content changed.

        Args:
            user_id: UUID of the user to sync.

        Returns:
            UserSyncResult with sync outcome details.
        """
        result = UserSyncResult(user_id=user_id)

        for attempt in range(self.max_retries + 1):
            try:
                # Retrieve current memory state
                memory_state = await self.memory_manager.get_memory_state(user_id)

                # Check if short-term memory needs flushing
                short_term_flushed = await self._flush_short_term_if_expired(
                    user_id, memory_state
                )
                result.short_term_flushed = short_term_flushed

                # Persist long-term memory updates
                long_term_updated = await self._persist_long_term_memory(
                    user_id, memory_state
                )
                result.long_term_updated = long_term_updated

                # Trigger embedding update if memory content changed
                if short_term_flushed or long_term_updated:
                    result.embedding_triggered = await self._trigger_embedding_update(
                        user_id, memory_state
                    )

                return result

            except Exception as exc:
                if attempt < self.max_retries:
                    logger.warning(
                        "Sync attempt %d/%d failed for user %s: %s",
                        attempt + 1,
                        self.max_retries + 1,
                        user_id,
                        exc,
                    )
                    await asyncio.sleep(0.5 * (attempt + 1))  # Backoff
                else:
                    result.error = str(exc)
                    logger.error(
                        "All sync attempts failed for user %s: %s", user_id, exc
                    )

        return result

    async def cleanup_stale_memories(self) -> int:
        """Detect and clean up stale short-term memory entries.

        Identifies users whose short-term memory has exceeded the
        stale threshold and flushes their expired session data.

        Returns:
            Number of stale entries cleaned.
        """
        cleaned = 0

        try:
            user_ids = await self._get_active_user_ids()
            cutoff = datetime.now(timezone.utc) - timedelta(
                hours=self.stale_threshold_hours
            )

            for user_id in user_ids:
                try:
                    memory_state = await self.memory_manager.get_memory_state(user_id)

                    last_ts = memory_state.short_term.last_interaction_timestamp
                    if last_ts and last_ts < cutoff:
                        # Session is stale — clear short-term memory
                        await self.memory_manager.clear_short_term_memory(user_id)
                        cleaned += 1
                        logger.debug(
                            "Cleaned stale short-term memory for user %s (last activity: %s)",
                            user_id,
                            last_ts.isoformat(),
                        )

                except Exception as exc:
                    logger.warning(
                        "Failed to check/clean stale memory for user %s: %s",
                        user_id,
                        exc,
                    )

            if cleaned:
                logger.info("Cleaned %d stale memory entries", cleaned)

        except Exception as exc:
            logger.error("Stale memory cleanup failed: %s", exc)

        return cleaned

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def total_synced(self) -> int:
        return self._total_synced

    @property
    def total_errors(self) -> int:
        return self._total_errors

    @property
    def last_cycle_result(self) -> SyncCycleResult | None:
        return self._last_cycle_result

    # ------------------------------------------------------------------
    # Private Implementation
    # ------------------------------------------------------------------

    async def _run_loop(self) -> None:
        """Internal loop executing sync cycles at the configured interval."""
        while self._running:
            try:
                await self.run()
            except Exception as exc:
                logger.error("Unexpected error in memory sync loop: %s", exc)
            await asyncio.sleep(self.sync_interval_seconds)

    async def _get_active_user_ids(self) -> list[UUID]:
        """Retrieve user IDs that have active memory state.

        Returns users with non-empty memory JSONB. Override or extend
        for more sophisticated activity detection.
        """
        try:
            from sqlalchemy import select, text
            from app.models.user import User

            db = self.memory_repository._db
            stmt = (
                select(User.id)
                .where(User.memory != text("'{}'::jsonb"))
                .limit(self.batch_size * 10)
            )
            result = await db.execute(stmt)
            return [row[0] for row in result.all()]

        except Exception as exc:
            logger.error("Failed to fetch active user IDs: %s", exc)
            return []

    async def _flush_short_term_if_expired(
        self,
        user_id: UUID,
        memory_state: Any,
    ) -> bool:
        """Flush short-term memory to long-term if expired.

        Promotes useful short-term data (recent queries, cart state)
        to long-term patterns before clearing the session context.
        """
        last_ts = memory_state.short_term.last_interaction_timestamp
        if not last_ts:
            return False

        cutoff = datetime.now(timezone.utc) - timedelta(
            hours=self.stale_threshold_hours
        )

        if last_ts >= cutoff:
            return False  # Not expired yet

        # Promote useful signals to long-term memory
        await self._promote_to_long_term(user_id, memory_state)

        # Clear the expired short-term memory
        await self.memory_manager.clear_short_term_memory(user_id)

        logger.debug("Flushed short-term memory for user %s", user_id)
        return True

    async def _promote_to_long_term(
        self,
        user_id: UUID,
        memory_state: Any,
    ) -> None:
        """Extract durable signals from short-term memory and promote them."""
        try:
            updates: dict[str, Any] = {}

            # Promote recent queries as behavioral pattern signals
            recent_queries = memory_state.short_term.recent_queries
            if recent_queries:
                existing_patterns = list(memory_state.long_term.purchase_patterns)
                # Keep unique patterns, limit growth
                for query in recent_queries[:5]:
                    if query not in existing_patterns:
                        existing_patterns.append(query)
                updates["purchase_patterns"] = existing_patterns[-20:]

            # Promote interaction count
            if memory_state.short_term.interaction_count > 0:
                updates["total_purchases"] = (
                    memory_state.long_term.total_purchases
                    + memory_state.short_term.interaction_count
                )

            # Promote urgency patterns
            urgency = memory_state.short_term.active_urgency_level
            if urgency:
                patterns = dict(memory_state.long_term.past_urgency_patterns)
                patterns[urgency] = patterns.get(urgency, 0) + 1
                updates["past_urgency_patterns"] = patterns

            if updates:
                await self.memory_manager.update_long_term_memory(user_id, updates)

        except Exception as exc:
            logger.warning(
                "Failed to promote short-term to long-term for user %s: %s",
                user_id,
                exc,
            )

    async def _persist_long_term_memory(
        self,
        user_id: UUID,
        memory_state: Any,
    ) -> bool:
        """Persist long-term memory to the repository (JSONB storage).

        Returns True if the memory was updated.
        """
        try:
            existing = await self.memory_repository.get_memory(user_id, "long_term")
            current_data = memory_state.long_term.model_dump()

            # Only write if there are actual changes
            if existing == current_data:
                return False

            await self.memory_repository.save_memory(
                user_id, "long_term", current_data
            )
            return True

        except Exception as exc:
            logger.warning(
                "Failed to persist long-term memory for user %s: %s",
                user_id,
                exc,
            )
            return False

    async def _trigger_embedding_update(
        self,
        user_id: UUID,
        memory_state: Any,
    ) -> bool:
        """Trigger a vector index update for changed memory content.

        Builds a text representation of long-term memory and syncs
        it to the FAISS memory index via VectorSync.
        """
        if self.vector_sync is None:
            return False

        try:
            # Build document for vector indexing
            long_term = memory_state.long_term
            text_parts: list[str] = []

            if long_term.dietary_preferences:
                text_parts.append(f"Dietary: {', '.join(long_term.dietary_preferences)}")
            if long_term.preferred_brands:
                text_parts.append(f"Brands: {', '.join(long_term.preferred_brands)}")
            if long_term.favorite_categories:
                text_parts.append(f"Categories: {', '.join(long_term.favorite_categories)}")
            if long_term.budget_level:
                text_parts.append(f"Budget: {long_term.budget_level}")
            if long_term.purchase_patterns:
                text_parts.append(f"Patterns: {', '.join(long_term.purchase_patterns[:10])}")

            if not text_parts:
                return False

            memory_doc = {
                "memory_id": f"user_memory_{user_id}",
                "content": " | ".join(text_parts),
                "user_id": str(user_id),
                "memory_type": "long_term",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

            await self.vector_sync.sync_memories(
                [memory_doc],
                id_field="memory_id",
                text_field="content",
            )

            logger.debug("Triggered embedding update for user %s", user_id)
            return True

        except Exception as exc:
            logger.warning(
                "Failed to trigger embedding update for user %s: %s",
                user_id,
                exc,
            )
            return False
