"""Semantic retrieval module for NeedNow AI.

Provides high-level semantic search over FAISS-indexed product and memory
vectors. Wraps FAISSManager search with query embedding, domain-specific
retrieval logic, and result ranking.

Dependencies:
    - FAISSManager: Vector index operations
    - Embedder: Query text → vector conversion
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.memory.embeddings.embedder import Embedder
from app.vectorstore.faiss_manager import FAISSManager, SearchResult

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class RetrieverError(Exception):
    """Base exception for retriever operations."""


class EmbeddingFailedError(RetrieverError):
    """Raised when query embedding generation fails."""


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class RankingStrategy(str, Enum):
    """Supported result ranking strategies."""

    RELEVANCE = "relevance"
    RECENCY = "recency"
    POPULARITY = "popularity"
    WEIGHTED = "weighted"


@dataclass
class RetrievalResult:
    """A single semantic retrieval result with enriched context."""

    id: str
    text: str | None = None
    score: float = 0.0
    rank: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    source_index: str = ""


@dataclass
class RetrievalResponse:
    """Structured response from a retrieval operation."""

    query: str
    results: list[RetrievalResult]
    total_found: int
    index_name: str
    strategy: RankingStrategy = RankingStrategy.RELEVANCE


# ---------------------------------------------------------------------------
# VectorRetriever
# ---------------------------------------------------------------------------


class VectorRetriever:
    """Semantic retrieval engine over FAISS vector indexes.

    Converts natural language queries into embeddings, searches the
    relevant FAISS index, and returns ranked results with metadata.

    Args:
        faiss_manager: FAISSManager instance for vector search.
        embedder: Embedder instance for query vectorization.
        product_index_name: Name of the product index.
        memory_index_name: Name of the memory index.
        default_top_k: Default number of results to return.
    """

    DEFAULT_PRODUCT_INDEX = "products"
    DEFAULT_MEMORY_INDEX = "user_memory"

    def __init__(
        self,
        faiss_manager: FAISSManager,
        embedder: Embedder,
        *,
        product_index_name: str | None = None,
        memory_index_name: str | None = None,
        default_top_k: int = 10,
    ) -> None:
        self.faiss_manager = faiss_manager
        self.embedder = embedder
        self.product_index_name = product_index_name or self.DEFAULT_PRODUCT_INDEX
        self.memory_index_name = memory_index_name or self.DEFAULT_MEMORY_INDEX
        self.default_top_k = default_top_k

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def retrieve_products(
        self,
        query: str,
        *,
        top_k: int | None = None,
        score_threshold: float = 0.0,
        filters: dict[str, Any] | None = None,
        strategy: RankingStrategy = RankingStrategy.RELEVANCE,
    ) -> RetrievalResponse:
        """Retrieve relevant products for a natural language query.

        Args:
            query: User search query or intent description.
            top_k: Maximum number of results.
            score_threshold: Minimum similarity score.
            filters: Optional metadata filters (e.g. {"category": "electronics"}).
            strategy: Ranking strategy to apply to results.

        Returns:
            RetrievalResponse with ranked product results.
        """
        k = top_k or self.default_top_k

        logger.info("Product retrieval: query='%s', top_k=%d", query, k)

        results = await self.semantic_search(
            query=query,
            index_name=self.product_index_name,
            top_k=k * 2 if filters else k,  # over-fetch when filtering
            score_threshold=score_threshold,
        )

        # Apply metadata filters
        if filters:
            results = self._apply_filters(results, filters)
            results = results[:k]

        # Rank results
        ranked = await self.rank_results(results, strategy=strategy)

        logger.info(
            "Product retrieval complete: %d results for '%s'",
            len(ranked),
            query,
        )

        return RetrievalResponse(
            query=query,
            results=ranked,
            total_found=len(ranked),
            index_name=self.product_index_name,
            strategy=strategy,
        )

    async def retrieve_memories(
        self,
        query: str,
        *,
        user_id: str | None = None,
        memory_type: str | None = None,
        top_k: int | None = None,
        score_threshold: float = 0.3,
        strategy: RankingStrategy = RankingStrategy.RECENCY,
    ) -> RetrievalResponse:
        """Retrieve relevant user memories for a query.

        Searches the memory index for contextually similar past
        interactions, preferences, or behavioral signals.

        Args:
            query: Query text describing the information need.
            user_id: Filter memories to a specific user.
            memory_type: Filter by memory type (preference/purchase/behavior).
            top_k: Maximum number of results.
            score_threshold: Minimum similarity score.
            strategy: Ranking strategy (defaults to recency for memories).

        Returns:
            RetrievalResponse with ranked memory results.
        """
        k = top_k or self.default_top_k

        logger.info(
            "Memory retrieval: query='%s', user_id=%s, type=%s",
            query,
            user_id,
            memory_type,
        )

        # Build filters from parameters
        filters: dict[str, Any] = {}
        if user_id:
            filters["user_id"] = user_id
        if memory_type:
            filters["memory_type"] = memory_type

        results = await self.semantic_search(
            query=query,
            index_name=self.memory_index_name,
            top_k=k * 3 if filters else k,  # over-fetch heavily for filtered memories
            score_threshold=score_threshold,
        )

        # Apply filters
        if filters:
            results = self._apply_filters(results, filters)
            results = results[:k]

        # Rank results
        ranked = await self.rank_results(results, strategy=strategy)

        logger.info(
            "Memory retrieval complete: %d results for '%s'",
            len(ranked),
            query,
        )

        return RetrievalResponse(
            query=query,
            results=ranked,
            total_found=len(ranked),
            index_name=self.memory_index_name,
            strategy=strategy,
        )

    async def semantic_search(
        self,
        query: str,
        index_name: str,
        *,
        top_k: int | None = None,
        score_threshold: float = 0.0,
    ) -> list[RetrievalResult]:
        """Perform raw semantic search on any FAISS index.

        Embeds the query and returns unranked results from the specified
        index. This is the low-level search primitive used by
        retrieve_products() and retrieve_memories().

        Args:
            query: Natural language query string.
            index_name: FAISS index to search.
            top_k: Maximum results.
            score_threshold: Minimum similarity score cutoff.

        Returns:
            List of RetrievalResult sorted by raw similarity score.

        Raises:
            EmbeddingFailedError: If query embedding generation fails.
            RetrieverError: If the search operation fails.
        """
        k = top_k or self.default_top_k

        # Generate query embedding
        try:
            embedding_result = await self.embedder.embed(query)
            query_vector = embedding_result.vector
        except Exception as exc:
            logger.error("Failed to embed query '%s': %s", query, exc)
            raise EmbeddingFailedError(
                f"Could not generate embedding for query: {exc}"
            ) from exc

        # Search FAISS index
        try:
            search_results: list[SearchResult] = await self.faiss_manager.search(
                index_name,
                query_vector,
                top_k=k,
                score_threshold=score_threshold,
            )
        except Exception as exc:
            logger.error("Search failed on index '%s': %s", index_name, exc)
            raise RetrieverError(
                f"Vector search failed on '{index_name}': {exc}"
            ) from exc

        # Convert to RetrievalResult
        results: list[RetrievalResult] = []
        for idx, sr in enumerate(search_results):
            results.append(
                RetrievalResult(
                    id=sr.id,
                    text=sr.metadata.get("title") or sr.metadata.get("content"),
                    score=sr.score,
                    rank=idx + 1,
                    metadata=sr.metadata,
                    source_index=index_name,
                )
            )

        logger.debug(
            "Semantic search on '%s': %d results (threshold=%.2f)",
            index_name,
            len(results),
            score_threshold,
        )

        return results

    async def rank_results(
        self,
        results: list[RetrievalResult],
        *,
        strategy: RankingStrategy = RankingStrategy.RELEVANCE,
        weights: dict[str, float] | None = None,
    ) -> list[RetrievalResult]:
        """Rank retrieval results using the specified strategy.

        Strategies:
            - RELEVANCE: Sort by similarity score (default).
            - RECENCY: Prioritize recent items (requires "created_at" metadata).
            - POPULARITY: Prioritize popular items (requires "popularity" metadata).
            - WEIGHTED: Combine multiple signals with configurable weights.

        Args:
            results: Unranked or pre-sorted results.
            strategy: Ranking strategy to apply.
            weights: Signal weights for WEIGHTED strategy.
                Defaults to {"relevance": 0.6, "recency": 0.2, "popularity": 0.2}.

        Returns:
            Re-ranked results with updated rank positions.
        """
        if not results:
            return []

        if strategy == RankingStrategy.RELEVANCE:
            ranked = self._rank_by_relevance(results)

        elif strategy == RankingStrategy.RECENCY:
            ranked = self._rank_by_recency(results)

        elif strategy == RankingStrategy.POPULARITY:
            ranked = self._rank_by_popularity(results)

        elif strategy == RankingStrategy.WEIGHTED:
            default_weights = {"relevance": 0.6, "recency": 0.2, "popularity": 0.2}
            ranked = self._rank_weighted(results, weights or default_weights)

        else:
            ranked = results

        # Assign final rank positions
        for idx, result in enumerate(ranked):
            result.rank = idx + 1

        return ranked

    # ------------------------------------------------------------------
    # Multi-Index Retrieval
    # ------------------------------------------------------------------

    async def retrieve_combined(
        self,
        query: str,
        *,
        product_top_k: int = 5,
        memory_top_k: int = 5,
        user_id: str | None = None,
    ) -> dict[str, RetrievalResponse]:
        """Retrieve from both product and memory indexes simultaneously.

        Useful for building context that combines product recommendations
        with user history.

        Args:
            query: Search query.
            product_top_k: Products to retrieve.
            memory_top_k: Memories to retrieve.
            user_id: Filter memories by user.

        Returns:
            Dict with "products" and "memories" RetrievalResponse entries.
        """
        products = await self.retrieve_products(query, top_k=product_top_k)
        memories = await self.retrieve_memories(
            query, top_k=memory_top_k, user_id=user_id
        )

        return {"products": products, "memories": memories}

    # ------------------------------------------------------------------
    # Private Ranking Implementations
    # ------------------------------------------------------------------

    @staticmethod
    def _rank_by_relevance(results: list[RetrievalResult]) -> list[RetrievalResult]:
        """Sort by similarity score, highest first."""
        return sorted(results, key=lambda r: r.score, reverse=True)

    @staticmethod
    def _rank_by_recency(results: list[RetrievalResult]) -> list[RetrievalResult]:
        """Sort by created_at metadata, most recent first.

        Falls back to score ordering for items without timestamp.
        """
        def sort_key(r: RetrievalResult) -> tuple[str, float]:
            ts = r.metadata.get("created_at", "")
            return (ts if ts else "0000-00-00", r.score)

        return sorted(results, key=sort_key, reverse=True)

    @staticmethod
    def _rank_by_popularity(results: list[RetrievalResult]) -> list[RetrievalResult]:
        """Sort by popularity metadata, highest first.

        Falls back to score ordering for items without popularity data.
        """
        def sort_key(r: RetrievalResult) -> tuple[float, float]:
            pop = float(r.metadata.get("popularity", 0.0))
            return (pop, r.score)

        return sorted(results, key=sort_key, reverse=True)

    @staticmethod
    def _rank_weighted(
        results: list[RetrievalResult],
        weights: dict[str, float],
    ) -> list[RetrievalResult]:
        """Compute a weighted composite score across multiple signals."""
        w_relevance = weights.get("relevance", 0.6)
        w_recency = weights.get("recency", 0.2)
        w_popularity = weights.get("popularity", 0.2)

        scored: list[tuple[float, RetrievalResult]] = []
        for r in results:
            relevance_score = r.score
            recency_score = _normalize_recency(r.metadata.get("created_at"))
            popularity_score = float(r.metadata.get("popularity", 0.0))

            composite = (
                w_relevance * relevance_score
                + w_recency * recency_score
                + w_popularity * popularity_score
            )
            scored.append((composite, r))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in scored]

    # ------------------------------------------------------------------
    # Private Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _apply_filters(
        results: list[RetrievalResult],
        filters: dict[str, Any],
    ) -> list[RetrievalResult]:
        """Filter results by metadata key-value equality."""
        filtered: list[RetrievalResult] = []
        for result in results:
            if all(
                result.metadata.get(key) == value
                for key, value in filters.items()
            ):
                filtered.append(result)
        return filtered


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _normalize_recency(timestamp: Any) -> float:
    """Convert a timestamp string to a 0-1 recency score.

    Simple heuristic: ISO-format strings sort lexicographically,
    so we use character ordinal sum normalized to a range.
    For production, parse into datetime and compute decay.
    """
    if not timestamp:
        return 0.0
    try:
        ts_str = str(timestamp)
        # Rough ordinal-based scoring for sorting purposes
        # Production: use actual datetime decay calculation
        ordinal_sum = sum(ord(c) for c in ts_str[:19])
        # Normalize to 0-1 (ISO timestamps ~range 950–1100 ordinal sum)
        return min(1.0, max(0.0, (ordinal_sum - 900) / 200))
    except (TypeError, ValueError):
        return 0.0
