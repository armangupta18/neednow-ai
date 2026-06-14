"""FAISS vector index manager.

Manages FAISS vector indexes for products, memories, and users.
Supports index lifecycle (create, load, save), vector CRUD, and
similarity search with configurable distance metrics.

Architecture:
    - FAISS for fast approximate nearest-neighbor search
    - In-memory index with on-disk persistence
    - Async-friendly interface for FastAPI integration
    - Compatible with future AWS deployment (S3-backed persistence)
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

try:
    import faiss
except ImportError:  # pragma: no cover
    faiss = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class FAISSManagerError(Exception):
    """Base exception for FAISSManager operations."""


class IndexNotFoundError(FAISSManagerError):
    """Raised when an index file cannot be located."""


class IndexAlreadyExistsError(FAISSManagerError):
    """Raised when attempting to create an index that already exists."""


@dataclass
class SearchResult:
    """A single search result from a FAISS query."""

    id: str
    score: float
    vector: list[float] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class FAISSManager:
    """Manages FAISS vector indexes for the NeedNow AI platform.

    Provides create/load/save lifecycle, vector add/remove, and
    similarity search. Designed for async FastAPI handlers via
    run_in_executor patterns.

    Args:
        dimensions: Embedding vector dimensionality.
        index_dir: Directory for persisting index files.
        metric: Distance metric — "cosine" (default) or "l2".
    """

    def __init__(
        self,
        dimensions: int = 1024,
        index_dir: str | Path = "./data/indexes",
        metric: str = "cosine",
    ) -> None:
        if faiss is None:
            raise FAISSManagerError(
                "faiss-cpu or faiss-gpu must be installed: pip install faiss-cpu"
            )

        self.dimensions = dimensions
        self.index_dir = Path(index_dir)
        self.metric = metric

        # Internal state
        self._indexes: dict[str, faiss.Index] = {}
        self._id_maps: dict[str, dict[str, int]] = {}  # name -> {ext_id -> faiss_pos}
        self._reverse_maps: dict[str, dict[int, str]] = {}  # name -> {faiss_pos -> ext_id}
        self._metadata_store: dict[str, dict[str, dict[str, Any]]] = {}  # name -> {ext_id -> meta}
        self._next_pos: dict[str, int] = {}

        logger.info(
            "FAISSManager initialized: dimensions=%d, metric=%s, index_dir=%s",
            dimensions,
            metric,
            self.index_dir,
        )

    # ------------------------------------------------------------------
    # Index Lifecycle
    # ------------------------------------------------------------------

    async def create_index(self, name: str, *, overwrite: bool = False) -> None:
        """Create a new FAISS index.

        Args:
            name: Logical index name (e.g., "products", "user_memory").
            overwrite: If True, replace an existing index with the same name.

        Raises:
            IndexAlreadyExistsError: If index exists and overwrite is False.
        """
        if name in self._indexes and not overwrite:
            raise IndexAlreadyExistsError(f"Index '{name}' already exists")

        index = self._build_index()
        self._indexes[name] = index
        self._id_maps[name] = {}
        self._reverse_maps[name] = {}
        self._metadata_store[name] = {}
        self._next_pos[name] = 0

        logger.info("Created index '%s' with %d dimensions", name, self.dimensions)

    async def load_index(self, name: str) -> None:
        """Load a persisted index from disk.

        Args:
            name: Logical index name matching a previously saved file.

        Raises:
            IndexNotFoundError: If the index file does not exist.
        """
        index_path = self.index_dir / f"{name}.faiss"
        if not index_path.exists():
            raise IndexNotFoundError(f"Index file not found: {index_path}")

        index = faiss.read_index(str(index_path))
        self._indexes[name] = index

        # Rebuild ID maps if metadata file exists
        self._id_maps.setdefault(name, {})
        self._reverse_maps.setdefault(name, {})
        self._metadata_store.setdefault(name, {})
        self._next_pos[name] = index.ntotal

        logger.info(
            "Loaded index '%s' from %s (%d vectors)",
            name,
            index_path,
            index.ntotal,
        )

    async def save_index(self, name: str) -> Path:
        """Persist an index to disk.

        Args:
            name: Logical index name.

        Returns:
            Path to the saved index file.

        Raises:
            FAISSManagerError: If the index does not exist in memory.
        """
        index = self._get_index(name)

        self.index_dir.mkdir(parents=True, exist_ok=True)
        index_path = self.index_dir / f"{name}.faiss"
        faiss.write_index(index, str(index_path))

        logger.info("Saved index '%s' to %s", name, index_path)
        return index_path

    # ------------------------------------------------------------------
    # Vector Operations
    # ------------------------------------------------------------------

    async def add_vectors(
        self,
        name: str,
        ids: list[str],
        vectors: list[list[float]],
        metadata: list[dict[str, Any]] | None = None,
    ) -> int:
        """Add vectors to a named index.

        Args:
            name: Target index name.
            ids: External string IDs for each vector.
            vectors: Embedding vectors to add.
            metadata: Optional metadata per vector.

        Returns:
            Number of vectors successfully added.

        Raises:
            FAISSManagerError: If index doesn't exist or inputs are invalid.
        """
        index = self._get_index(name)

        if len(ids) != len(vectors):
            raise FAISSManagerError(
                f"IDs count ({len(ids)}) must match vectors count ({len(vectors)})"
            )

        meta_list = metadata or [{}] * len(ids)
        np_vectors = self._prepare_vectors(vectors)

        # Add to FAISS
        index.add(np_vectors)

        # Update ID mappings
        for i, ext_id in enumerate(ids):
            pos = self._next_pos[name]
            self._id_maps[name][ext_id] = pos
            self._reverse_maps[name][pos] = ext_id
            self._metadata_store[name][ext_id] = meta_list[i]
            self._next_pos[name] += 1

        logger.debug("Added %d vectors to index '%s'", len(ids), name)
        return len(ids)

    async def remove_vectors(self, name: str, ids: list[str]) -> int:
        """Mark vectors as removed from a named index.

        Note: FAISS flat indexes do not support true deletion.
        This implementation removes from the ID map so they won't
        appear in search results. A full rebuild is needed to reclaim space.

        Args:
            name: Target index name.
            ids: External string IDs to remove.

        Returns:
            Number of vectors removed from the mapping.
        """
        self._get_index(name)  # validates existence
        removed = 0

        for ext_id in ids:
            if ext_id in self._id_maps[name]:
                pos = self._id_maps[name].pop(ext_id)
                self._reverse_maps[name].pop(pos, None)
                self._metadata_store[name].pop(ext_id, None)
                removed += 1

        logger.debug("Removed %d vectors from index '%s'", removed, name)
        return removed

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    async def search(
        self,
        name: str,
        query_vector: list[float],
        *,
        top_k: int = 10,
        score_threshold: float | None = None,
    ) -> list[SearchResult]:
        """Search for nearest neighbors in a named index.

        Args:
            name: Target index name.
            query_vector: Query embedding vector.
            top_k: Maximum number of results.
            score_threshold: Minimum similarity score (only for cosine metric).

        Returns:
            Ordered list of SearchResult, best match first.
        """
        index = self._get_index(name)

        if index.ntotal == 0:
            return []

        np_query = self._prepare_vectors([query_vector])
        distances, indices = index.search(np_query, min(top_k, index.ntotal))

        results: list[SearchResult] = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue

            ext_id = self._reverse_maps[name].get(int(idx))
            if ext_id is None:
                # Vector was soft-deleted
                continue

            score = self._distance_to_score(float(dist))
            if score_threshold is not None and score < score_threshold:
                continue

            results.append(
                SearchResult(
                    id=ext_id,
                    score=score,
                    metadata=self._metadata_store[name].get(ext_id, {}),
                )
            )

        logger.debug(
            "Search on '%s': top_k=%d, returned=%d", name, top_k, len(results)
        )
        return results

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    async def get_index_stats(self, name: str) -> dict[str, Any]:
        """Return stats for a named index."""
        index = self._get_index(name)
        return {
            "name": name,
            "total_vectors": index.ntotal,
            "dimensions": self.dimensions,
            "active_ids": len(self._id_maps[name]),
            "metric": self.metric,
        }

    async def list_indexes(self) -> list[str]:
        """Return names of all loaded indexes."""
        return list(self._indexes.keys())

    # ------------------------------------------------------------------
    # Private Helpers
    # ------------------------------------------------------------------

    def _get_index(self, name: str) -> faiss.Index:
        """Retrieve a loaded index by name."""
        if name not in self._indexes:
            raise FAISSManagerError(
                f"Index '{name}' not found. Call create_index() or load_index() first."
            )
        return self._indexes[name]

    def _build_index(self) -> faiss.Index:
        """Construct a new FAISS index based on the configured metric."""
        if self.metric == "cosine":
            # Inner-product on L2-normalized vectors == cosine similarity
            index = faiss.IndexFlatIP(self.dimensions)
        else:
            index = faiss.IndexFlatL2(self.dimensions)
        return index

    def _prepare_vectors(self, vectors: list[list[float]]) -> np.ndarray:
        """Convert list of vectors to a numpy array, normalizing for cosine."""
        arr = np.array(vectors, dtype=np.float32)

        if arr.ndim == 1:
            arr = arr.reshape(1, -1)

        if arr.shape[1] != self.dimensions:
            raise FAISSManagerError(
                f"Vector dimension mismatch: expected {self.dimensions}, got {arr.shape[1]}"
            )

        if self.metric == "cosine":
            faiss.normalize_L2(arr)

        return arr

    def _distance_to_score(self, distance: float) -> float:
        """Convert raw FAISS distance to a 0-1 similarity score."""
        if self.metric == "cosine":
            # Inner-product on normalized vectors already gives cosine similarity
            return float(distance)
        # L2 → similarity approximation
        return 1.0 / (1.0 + distance)
