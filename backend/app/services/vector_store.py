"""ChromaDB vector store for NeedNow AI.

Provides persistent vector storage with cosine similarity search
for product embeddings. Uses ChromaDB with on-disk persistence.

Storage path: datasets/embeddings/chroma_db
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class VectorStoreError(Exception):
    """Base exception for vector store operations."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class ProductNotFoundError(VectorStoreError):
    """Raised when a product is not found in the vector store."""


# ---------------------------------------------------------------------------
# Result Model
# ---------------------------------------------------------------------------


@dataclass
class SearchResult:
    """A single product search result."""

    id: str
    title: str
    category: str
    rating: float
    distance: float
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def similarity_score(self) -> float:
        """Convert cosine distance to similarity (1 - distance)."""
        return 1.0 - self.distance


# ---------------------------------------------------------------------------
# Vector Store
# ---------------------------------------------------------------------------


class VectorStore:
    """ChromaDB-backed persistent vector store for product embeddings.

    Stores product embeddings with metadata (parent_asin, title, category,
    rating) and supports cosine similarity search.

    Args:
        persist_dir: Path to ChromaDB persistent storage directory.
        collection_name: Name of the ChromaDB collection.
    """

    DEFAULT_PERSIST_DIR = "datasets/embeddings/chroma_db"
    DEFAULT_COLLECTION = "products"

    def __init__(
        self,
        persist_dir: str | Path | None = None,
        collection_name: str = DEFAULT_COLLECTION,
    ) -> None:
        self._persist_dir = str(persist_dir or self.DEFAULT_PERSIST_DIR)
        self._collection_name = collection_name

        # Ensure directory exists
        Path(self._persist_dir).mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client with persistent storage
        self._client = chromadb.PersistentClient(
            path=self._persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )

        # Get or create collection with cosine distance
        self._collection = self._client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        logger.info(
            "VectorStore initialized: persist_dir=%s, collection=%s, count=%d",
            self._persist_dir,
            self._collection_name,
            self._collection.count(),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_product(
        self,
        embedding: list[float],
        parent_asin: str,
        title: str,
        category: str,
        rating: float = 0.0,
    ) -> None:
        """Add a single product embedding to the vector store.

        Args:
            embedding: Vector embedding (e.g., 384 dimensions).
            parent_asin: Unique product identifier (used as ChromaDB ID).
            title: Product title.
            category: Product category.
            rating: Average product rating.

        Raises:
            VectorStoreError: If the insertion fails.
        """
        try:
            self._collection.upsert(
                ids=[parent_asin],
                embeddings=[embedding],
                metadatas=[
                    {
                        "parent_asin": parent_asin,
                        "title": title[:500],
                        "category": category[:255],
                        "rating": float(rating),
                    }
                ],
                documents=[title],
            )
            logger.debug("Added product: %s", parent_asin)

        except Exception as exc:
            logger.error("Failed to add product %s: %s", parent_asin, exc)
            raise VectorStoreError(
                f"Failed to add product '{parent_asin}': {exc}"
            ) from exc

    def add_products(
        self,
        embeddings: list[list[float]],
        parent_asins: list[str],
        titles: list[str],
        categories: list[str],
        ratings: list[float],
        *,
        batch_size: int = 500,
    ) -> int:
        """Add multiple product embeddings in batches.

        Args:
            embeddings: List of embedding vectors.
            parent_asins: List of product IDs.
            titles: List of product titles.
            categories: List of product categories.
            ratings: List of average ratings.
            batch_size: Records per ChromaDB upsert call.

        Returns:
            Number of products successfully added.

        Raises:
            VectorStoreError: If a batch insertion fails.
        """
        if not embeddings:
            return 0

        total = len(embeddings)
        added = 0

        try:
            for start in range(0, total, batch_size):
                end = min(start + batch_size, total)

                batch_ids = parent_asins[start:end]
                batch_embeddings = embeddings[start:end]
                batch_titles = titles[start:end]
                batch_categories = categories[start:end]
                batch_ratings = ratings[start:end]

                batch_metadatas = [
                    {
                        "parent_asin": asin,
                        "title": title[:500],
                        "category": cat[:255],
                        "rating": float(r),
                    }
                    for asin, title, cat, r in zip(
                        batch_ids, batch_titles, batch_categories, batch_ratings
                    )
                ]

                self._collection.upsert(
                    ids=batch_ids,
                    embeddings=batch_embeddings,
                    metadatas=batch_metadatas,
                    documents=batch_titles,
                )

                added += len(batch_ids)
                logger.debug(
                    "Batch upserted: %d/%d products", added, total
                )

            logger.info("Added %d products to vector store", added)
            return added

        except Exception as exc:
            logger.error("Batch add failed at %d/%d: %s", added, total, exc)
            raise VectorStoreError(
                f"Batch insertion failed after {added} products: {exc}"
            ) from exc

    def search_products(
        self,
        query_embedding: list[float],
        *,
        top_k: int = 10,
        category: str | None = None,
        min_rating: float | None = None,
    ) -> list[SearchResult]:
        """Search for similar products using cosine similarity.

        Args:
            query_embedding: Query vector to search against.
            top_k: Maximum number of results to return.
            category: Optional category filter.
            min_rating: Optional minimum rating filter.

        Returns:
            List of SearchResult ordered by similarity (highest first).

        Raises:
            VectorStoreError: If the search operation fails.
        """
        try:
            # Build where filter
            where_filter = self._build_filter(category=category, min_rating=min_rating)

            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_filter,
                include=["metadatas", "distances", "documents"],
            )

            # Parse results
            search_results: list[SearchResult] = []

            if not results["ids"] or not results["ids"][0]:
                return search_results

            ids = results["ids"][0]
            distances = results["distances"][0] if results["distances"] else [0.0] * len(ids)
            metadatas = results["metadatas"][0] if results["metadatas"] else [{}] * len(ids)

            for doc_id, distance, metadata in zip(ids, distances, metadatas):
                search_results.append(
                    SearchResult(
                        id=doc_id,
                        title=metadata.get("title", ""),
                        category=metadata.get("category", ""),
                        rating=float(metadata.get("rating", 0.0)),
                        distance=float(distance),
                        metadata=metadata,
                    )
                )

            logger.debug(
                "Search returned %d results (top_k=%d)", len(search_results), top_k
            )
            return search_results

        except Exception as exc:
            logger.error("Product search failed: %s", exc)
            raise VectorStoreError(f"Search failed: {exc}") from exc

    def delete_product(self, parent_asin: str) -> None:
        """Delete a product from the vector store.

        Args:
            parent_asin: Product ID to delete.

        Raises:
            VectorStoreError: If the deletion fails.
        """
        try:
            self._collection.delete(ids=[parent_asin])
            logger.info("Deleted product: %s", parent_asin)

        except Exception as exc:
            logger.error("Failed to delete product %s: %s", parent_asin, exc)
            raise VectorStoreError(
                f"Failed to delete product '{parent_asin}': {exc}"
            ) from exc

    def count(self) -> int:
        """Return the total number of products in the vector store.

        Returns:
            Integer count of stored embeddings.
        """
        try:
            return self._collection.count()
        except Exception as exc:
            logger.error("Failed to count products: %s", exc)
            raise VectorStoreError(f"Count failed: {exc}") from exc

    # ------------------------------------------------------------------
    # Private Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_filter(
        category: str | None = None,
        min_rating: float | None = None,
    ) -> dict[str, Any] | None:
        """Build a ChromaDB where filter from optional params."""
        conditions: list[dict[str, Any]] = []

        if category:
            conditions.append({"category": {"$eq": category}})

        if min_rating is not None:
            conditions.append({"rating": {"$gte": min_rating}})

        if not conditions:
            return None

        if len(conditions) == 1:
            return conditions[0]

        return {"$and": conditions}
