"""Vector sync module for NeedNow AI.

Keeps FAISS vector indexes synchronized with upstream database updates.
Detects stale indexes, performs incremental syncs for products and
memories, and triggers full rebuilds when drift exceeds thresholds.

Dependencies:
    - FAISSManager: Vector index lifecycle and operations.
    - IndexBuilder: Index construction and rebuild logic.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Awaitable

from app.vectorstore.faiss_manager import FAISSManager, FAISSManagerError
from app.vectorstore.index_builder import IndexBuilder, IndexBuildResult

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Type Aliases
# ---------------------------------------------------------------------------

DataFetchFn = Callable[[], Awaitable[list[dict[str, Any]]]]
"""Async callable that returns a list of document dicts from the data source."""


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class SyncError(Exception):
    """Base exception for sync operations."""


class StaleIndexError(SyncError):
    """Raised when an index is detected as stale beyond acceptable limits."""


# ---------------------------------------------------------------------------
# Enums & Schemas
# ---------------------------------------------------------------------------


class SyncStatus(str, Enum):
    """Status of a sync operation."""

    IDLE = "idle"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


class ChangeType(str, Enum):
    """Types of detected data changes."""

    ADDED = "added"
    MODIFIED = "modified"
    REMOVED = "removed"


@dataclass
class ChangeSet:
    """Detected changes between an index and its data source."""

    index_name: str
    added_ids: list[str] = field(default_factory=list)
    modified_ids: list[str] = field(default_factory=list)
    removed_ids: list[str] = field(default_factory=list)
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def total_changes(self) -> int:
        return len(self.added_ids) + len(self.modified_ids) + len(self.removed_ids)

    @property
    def has_changes(self) -> bool:
        return self.total_changes > 0

    @property
    def drift_ratio(self) -> float:
        """Ratio of changed items to total indexed items (approximate)."""
        total = len(self.added_ids) + len(self.modified_ids) + len(self.removed_ids)
        # Use sum of existing + added as denominator estimate
        denominator = max(1, len(self.modified_ids) + len(self.removed_ids) + len(self.added_ids))
        return total / denominator


@dataclass
class SyncResult:
    """Summary of a sync operation."""

    index_name: str
    status: SyncStatus
    vectors_added: int = 0
    vectors_removed: int = 0
    vectors_modified: int = 0
    duration_ms: float = 0.0
    rebuild_triggered: bool = False
    change_set: ChangeSet | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None


# ---------------------------------------------------------------------------
# VectorSync
# ---------------------------------------------------------------------------


class VectorSync:
    """Keeps vector indexes synchronized with upstream data sources.

    Supports both incremental sync (add/remove individual vectors) and
    full rebuild (when drift exceeds a threshold). Designed for periodic
    background execution via FastAPI BackgroundTasks or async scheduling.

    Args:
        faiss_manager: FAISSManager instance for vector operations.
        index_builder: IndexBuilder for full index rebuilds.
        rebuild_threshold: Drift ratio (0-1) above which a full rebuild
            is triggered instead of an incremental sync.
        embed_fn: Async callable for embedding new/modified document text.
    """

    DEFAULT_PRODUCT_INDEX = "products"
    DEFAULT_MEMORY_INDEX = "user_memory"

    def __init__(
        self,
        faiss_manager: FAISSManager,
        index_builder: IndexBuilder,
        *,
        rebuild_threshold: float = 0.3,
        embed_fn: Callable[[str], Awaitable[list[float]]] | None = None,
    ) -> None:
        self.faiss_manager = faiss_manager
        self.index_builder = index_builder
        self.rebuild_threshold = rebuild_threshold
        self._embed_fn = embed_fn
        self._sync_history: list[SyncResult] = []
        self._last_sync: dict[str, datetime] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def sync_products(
        self,
        products: list[dict[str, Any]],
        *,
        index_name: str | None = None,
        id_field: str = "asin",
        text_field: str = "title",
        force_rebuild: bool = False,
    ) -> SyncResult:
        """Synchronize the product index with the latest product catalog.

        Detects changes between the current index and the provided product
        data, then performs an incremental update or full rebuild.

        Args:
            products: Current complete product catalog.
            index_name: Index name (defaults to "products").
            id_field: Key for product ID in the data dicts.
            text_field: Key for the text field to embed.
            force_rebuild: If True, skip change detection and rebuild fully.

        Returns:
            SyncResult summarizing the operation.
        """
        name = index_name or self.DEFAULT_PRODUCT_INDEX
        start = time.perf_counter()
        started_at = datetime.now(timezone.utc)

        logger.info("Starting product sync for index '%s' (%d products)", name, len(products))

        try:
            if force_rebuild:
                return await self._do_full_rebuild(
                    name, products, id_field=id_field, text_field=text_field, started_at=started_at
                )

            # Detect changes
            change_set = await self.detect_changes(name, products, id_field=id_field)

            if not change_set.has_changes:
                logger.info("Product index '%s' is up to date — no changes detected", name)
                return self._build_result(
                    name, SyncStatus.SKIPPED, started_at=started_at, change_set=change_set
                )

            # Decide: incremental vs rebuild
            result = await self.rebuild_if_needed(
                name, products, change_set, id_field=id_field, text_field=text_field
            )
            result.started_at = started_at
            result.completed_at = datetime.now(timezone.utc)
            result.duration_ms = (time.perf_counter() - start) * 1000

            self._last_sync[name] = datetime.now(timezone.utc)
            self._sync_history.append(result)
            return result

        except Exception as exc:
            logger.error("Product sync failed for '%s': %s", name, exc)
            result = self._build_result(
                name, SyncStatus.FAILED, started_at=started_at, error=str(exc)
            )
            result.duration_ms = (time.perf_counter() - start) * 1000
            self._sync_history.append(result)
            return result

    async def sync_memories(
        self,
        memories: list[dict[str, Any]],
        *,
        index_name: str | None = None,
        id_field: str = "memory_id",
        text_field: str = "content",
        user_id: str | None = None,
        force_rebuild: bool = False,
    ) -> SyncResult:
        """Synchronize the memory index with the latest user memory data.

        Args:
            memories: Current complete memory dataset.
            index_name: Index name (defaults to "user_memory").
            id_field: Key for memory ID.
            text_field: Key for memory text content.
            user_id: If provided, only sync memories for this user.
            force_rebuild: If True, skip detection and rebuild fully.

        Returns:
            SyncResult summarizing the operation.
        """
        name = index_name or self.DEFAULT_MEMORY_INDEX
        start = time.perf_counter()
        started_at = datetime.now(timezone.utc)

        # Optionally filter by user
        if user_id:
            memories = [m for m in memories if m.get("user_id") == user_id]

        logger.info(
            "Starting memory sync for index '%s' (%d memories, user=%s)",
            name,
            len(memories),
            user_id or "all",
        )

        try:
            if force_rebuild:
                return await self._do_full_rebuild(
                    name, memories, id_field=id_field, text_field=text_field, started_at=started_at
                )

            # Detect changes
            change_set = await self.detect_changes(name, memories, id_field=id_field)

            if not change_set.has_changes:
                logger.info("Memory index '%s' is up to date", name)
                return self._build_result(
                    name, SyncStatus.SKIPPED, started_at=started_at, change_set=change_set
                )

            # Decide: incremental vs rebuild
            result = await self.rebuild_if_needed(
                name, memories, change_set, id_field=id_field, text_field=text_field
            )
            result.started_at = started_at
            result.completed_at = datetime.now(timezone.utc)
            result.duration_ms = (time.perf_counter() - start) * 1000

            self._last_sync[name] = datetime.now(timezone.utc)
            self._sync_history.append(result)
            return result

        except Exception as exc:
            logger.error("Memory sync failed for '%s': %s", name, exc)
            result = self._build_result(
                name, SyncStatus.FAILED, started_at=started_at, error=str(exc)
            )
            result.duration_ms = (time.perf_counter() - start) * 1000
            self._sync_history.append(result)
            return result

    async def detect_changes(
        self,
        index_name: str,
        documents: list[dict[str, Any]],
        *,
        id_field: str = "id",
    ) -> ChangeSet:
        """Detect changes between the current index and a document set.

        Compares indexed IDs against provided document IDs to identify
        additions, removals, and modifications.

        Args:
            index_name: Index to compare against.
            documents: Current source-of-truth document set.
            id_field: Key for document ID.

        Returns:
            ChangeSet describing all detected differences.
        """
        # Get currently indexed IDs
        try:
            stats = await self.faiss_manager.get_index_stats(index_name)
            indexed_ids = set(self.faiss_manager._id_maps.get(index_name, {}).keys())
        except FAISSManagerError:
            # Index doesn't exist yet — everything is "added"
            all_ids = [str(doc.get(id_field, "")) for doc in documents if doc.get(id_field)]
            return ChangeSet(
                index_name=index_name,
                added_ids=all_ids,
            )

        # Compute source IDs
        source_ids = set()
        source_map: dict[str, dict[str, Any]] = {}
        for doc in documents:
            doc_id = str(doc.get(id_field, ""))
            if doc_id:
                source_ids.add(doc_id)
                source_map[doc_id] = doc

        # Determine changes
        added_ids = list(source_ids - indexed_ids)
        removed_ids = list(indexed_ids - source_ids)

        # Detect modifications (check metadata hash if available)
        modified_ids: list[str] = []
        common_ids = source_ids & indexed_ids
        metadata_store = self.faiss_manager._metadata_store.get(index_name, {})

        for doc_id in common_ids:
            stored_meta = metadata_store.get(doc_id, {})
            current_doc = source_map.get(doc_id, {})

            # Simple modification detection: compare a checksum field if present
            stored_hash = stored_meta.get("_content_hash")
            current_hash = current_doc.get("_content_hash")

            if stored_hash and current_hash and stored_hash != current_hash:
                modified_ids.append(doc_id)
            elif "updated_at" in current_doc and "updated_at" in stored_meta:
                if str(current_doc["updated_at"]) != str(stored_meta.get("updated_at")):
                    modified_ids.append(doc_id)

        change_set = ChangeSet(
            index_name=index_name,
            added_ids=added_ids,
            modified_ids=modified_ids,
            removed_ids=removed_ids,
        )

        logger.info(
            "Change detection for '%s': +%d added, ~%d modified, -%d removed",
            index_name,
            len(added_ids),
            len(modified_ids),
            len(removed_ids),
        )

        return change_set

    async def rebuild_if_needed(
        self,
        index_name: str,
        documents: list[dict[str, Any]],
        change_set: ChangeSet,
        *,
        id_field: str = "id",
        text_field: str = "text",
    ) -> SyncResult:
        """Decide whether to perform an incremental sync or full rebuild.

        If the drift ratio exceeds the configured threshold, a full
        rebuild is triggered. Otherwise, performs incremental add/remove.

        Args:
            index_name: Target index.
            documents: Full document set (needed for rebuild).
            change_set: Detected changes from detect_changes().
            id_field: Key for document ID.
            text_field: Key for text content.

        Returns:
            SyncResult summarizing the action taken.
        """
        started_at = datetime.now(timezone.utc)

        # Check if drift exceeds threshold
        try:
            stats = await self.faiss_manager.get_index_stats(index_name)
            total_indexed = stats.get("total_vectors", 0)
        except FAISSManagerError:
            total_indexed = 0

        # Compute drift relative to index size
        if total_indexed > 0:
            drift = change_set.total_changes / total_indexed
        else:
            drift = 1.0  # Empty index → always rebuild

        if drift >= self.rebuild_threshold:
            logger.info(
                "Drift ratio %.2f exceeds threshold %.2f — triggering full rebuild for '%s'",
                drift,
                self.rebuild_threshold,
                index_name,
            )
            return await self._do_full_rebuild(
                index_name, documents, id_field=id_field, text_field=text_field, started_at=started_at
            )

        # Incremental sync
        return await self._do_incremental_sync(
            index_name, documents, change_set, id_field=id_field, text_field=text_field, started_at=started_at
        )

    # ------------------------------------------------------------------
    # Utility Methods
    # ------------------------------------------------------------------

    async def get_sync_history(
        self,
        *,
        index_name: str | None = None,
        limit: int = 20,
    ) -> list[SyncResult]:
        """Return recent sync results, optionally filtered by index."""
        history = self._sync_history
        if index_name:
            history = [r for r in history if r.index_name == index_name]
        return history[-limit:]

    async def get_last_sync_time(self, index_name: str) -> datetime | None:
        """Return the timestamp of the last successful sync for an index."""
        return self._last_sync.get(index_name)

    async def is_index_stale(
        self,
        index_name: str,
        max_age_seconds: float = 3600.0,
    ) -> bool:
        """Check whether an index is stale based on last sync time.

        Args:
            index_name: Index to check.
            max_age_seconds: Maximum allowed age in seconds (default 1 hour).

        Returns:
            True if the index hasn't been synced within the max age.
        """
        last = self._last_sync.get(index_name)
        if last is None:
            return True

        age = (datetime.now(timezone.utc) - last).total_seconds()
        is_stale = age > max_age_seconds

        if is_stale:
            logger.warning(
                "Index '%s' is stale: last synced %.0f seconds ago (max: %.0f)",
                index_name,
                age,
                max_age_seconds,
            )

        return is_stale

    # ------------------------------------------------------------------
    # Private Implementation
    # ------------------------------------------------------------------

    async def _do_full_rebuild(
        self,
        index_name: str,
        documents: list[dict[str, Any]],
        *,
        id_field: str = "id",
        text_field: str = "text",
        started_at: datetime | None = None,
    ) -> SyncResult:
        """Execute a full index rebuild."""
        started_at = started_at or datetime.now(timezone.utc)
        start = time.perf_counter()

        logger.info("Full rebuild starting for index '%s' (%d documents)", index_name, len(documents))

        build_result: IndexBuildResult = await self.index_builder.rebuild_index(
            index_name,
            documents,
            id_field=id_field,
            text_field=text_field,
        )

        elapsed = (time.perf_counter() - start) * 1000

        if build_result.success:
            result = SyncResult(
                index_name=index_name,
                status=SyncStatus.COMPLETED,
                vectors_added=build_result.vectors_added,
                duration_ms=elapsed,
                rebuild_triggered=True,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
            )
            self._last_sync[index_name] = datetime.now(timezone.utc)
        else:
            result = SyncResult(
                index_name=index_name,
                status=SyncStatus.FAILED,
                duration_ms=elapsed,
                rebuild_triggered=True,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                error=build_result.error,
            )

        self._sync_history.append(result)
        return result

    async def _do_incremental_sync(
        self,
        index_name: str,
        documents: list[dict[str, Any]],
        change_set: ChangeSet,
        *,
        id_field: str = "id",
        text_field: str = "text",
        started_at: datetime | None = None,
    ) -> SyncResult:
        """Execute an incremental sync (add new, re-embed modified, remove deleted)."""
        started_at = started_at or datetime.now(timezone.utc)
        start = time.perf_counter()

        logger.info(
            "Incremental sync for '%s': +%d, ~%d, -%d",
            index_name,
            len(change_set.added_ids),
            len(change_set.modified_ids),
            len(change_set.removed_ids),
        )

        # Build doc lookup
        doc_map = {str(doc.get(id_field, "")): doc for doc in documents}

        added = 0
        removed = 0
        modified = 0

        # Remove deleted vectors
        if change_set.removed_ids:
            removed = await self.faiss_manager.remove_vectors(index_name, change_set.removed_ids)

        # Remove modified vectors (will re-add with new embeddings)
        if change_set.modified_ids:
            await self.faiss_manager.remove_vectors(index_name, change_set.modified_ids)

        # Embed and add new + modified vectors
        ids_to_add = change_set.added_ids + change_set.modified_ids
        if ids_to_add and self._embed_fn:
            batch_ids: list[str] = []
            batch_vectors: list[list[float]] = []
            batch_metadata: list[dict[str, Any]] = []

            for doc_id in ids_to_add:
                doc = doc_map.get(doc_id)
                if not doc:
                    continue

                text = doc.get(text_field, "")
                if not text:
                    continue

                vector = await self._embed_fn(text)
                meta = {k: v for k, v in doc.items() if k not in (id_field, text_field)}

                batch_ids.append(doc_id)
                batch_vectors.append(vector)
                batch_metadata.append(meta)

            if batch_ids:
                count = await self.faiss_manager.add_vectors(
                    index_name, batch_ids, batch_vectors, batch_metadata
                )
                # Distinguish between new additions and modifications
                new_count = len([i for i in batch_ids if i in change_set.added_ids])
                mod_count = len([i for i in batch_ids if i in change_set.modified_ids])
                added = new_count
                modified = mod_count

        elif ids_to_add and not self._embed_fn:
            logger.warning(
                "Cannot embed new/modified vectors: no embed_fn configured"
            )

        elapsed = (time.perf_counter() - start) * 1000

        result = SyncResult(
            index_name=index_name,
            status=SyncStatus.COMPLETED,
            vectors_added=added,
            vectors_removed=removed,
            vectors_modified=modified,
            duration_ms=elapsed,
            rebuild_triggered=False,
            change_set=change_set,
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
        )

        logger.info(
            "Incremental sync complete for '%s': +%d, ~%d, -%d (%.1fms)",
            index_name,
            added,
            modified,
            removed,
            elapsed,
        )

        return result

    def _build_result(
        self,
        index_name: str,
        status: SyncStatus,
        *,
        started_at: datetime | None = None,
        change_set: ChangeSet | None = None,
        error: str | None = None,
    ) -> SyncResult:
        """Helper to construct a SyncResult."""
        return SyncResult(
            index_name=index_name,
            status=status,
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
            change_set=change_set,
            error=error,
        )
