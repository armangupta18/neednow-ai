"""Embedding-based retrieval module.

Performs similarity search over stored embedding vectors
to retrieve contextually relevant memory fragments.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class RetrievalResult:
    """A single result from a similarity search."""

    text: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


class EmbeddingRetriever:
    """Retrieves relevant text chunks via cosine similarity over embeddings.

    Maintains an in-memory vector store; suitable for per-session
    retrieval. For production persistence, back with a vector DB.
    """

    def __init__(self, similarity_threshold: float = 0.0) -> None:
        self.similarity_threshold = similarity_threshold
        self._vectors: list[np.ndarray] = []
        self._texts: list[str] = []
        self._metadata: list[dict[str, Any]] = []

    async def add(
        self,
        text: str,
        vector: list[float],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Index a text chunk with its embedding vector."""
        self._vectors.append(np.array(vector, dtype=np.float32))
        self._texts.append(text)
        self._metadata.append(metadata or {})

    async def add_batch(
        self,
        texts: list[str],
        vectors: list[list[float]],
        metadata_list: list[dict[str, Any]] | None = None,
    ) -> None:
        """Index multiple text chunks at once."""
        if metadata_list is None:
            metadata_list = [{}] * len(texts)

        for text, vector, meta in zip(texts, vectors, metadata_list):
            await self.add(text, vector, meta)

    async def retrieve(
        self,
        query_vector: list[float],
        *,
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        """Find the top-k most similar chunks to the query vector."""
        if not self._vectors:
            return []

        query = np.array(query_vector, dtype=np.float32)
        scores = [self._cosine_similarity(query, vec) for vec in self._vectors]

        # Pair scores with indices and sort descending
        scored_indices = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)

        results: list[RetrievalResult] = []
        for idx, score in scored_indices[:top_k]:
            if score < self.similarity_threshold:
                continue
            results.append(
                RetrievalResult(
                    text=self._texts[idx],
                    score=float(score),
                    metadata=self._metadata[idx],
                )
            )

        return results

    async def count(self) -> int:
        """Return the number of indexed vectors."""
        return len(self._vectors)

    async def clear(self) -> None:
        """Remove all indexed data."""
        self._vectors.clear()
        self._texts.clear()
        self._metadata.clear()

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        dot = float(np.dot(a, b))
        norm_a = float(np.linalg.norm(a))
        norm_b = float(np.linalg.norm(b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
