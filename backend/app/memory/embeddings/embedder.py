"""Embedding generation module.

Provides a unified interface for generating vector embeddings
from text using configurable model backends (e.g., Amazon Bedrock, OpenAI).
"""

from __future__ import annotations

from typing import Any

import numpy as np
from pydantic import BaseModel, Field


class EmbeddingResult(BaseModel):
    """Result of an embedding operation."""

    text: str = Field(..., description="Original input text")
    vector: list[float] = Field(..., description="Generated embedding vector")
    model: str = Field(default="", description="Model used for generation")
    dimensions: int = Field(default=0, description="Vector dimensionality")

    class Config:
        arbitrary_types_allowed = True


class Embedder:
    """Generates vector embeddings from text input.

    Designed as a pluggable abstraction — swap the underlying model
    by providing a different embedding function at init time.
    """

    def __init__(
        self,
        model_id: str = "amazon.titan-embed-text-v2:0",
        dimensions: int = 1024,
        embedding_fn: Any | None = None,
    ) -> None:
        self.model_id = model_id
        self.dimensions = dimensions
        self._embedding_fn = embedding_fn

    async def embed(self, text: str) -> EmbeddingResult:
        """Generate an embedding vector for a single text input."""
        if self._embedding_fn is not None:
            vector = await self._embedding_fn(text)
        else:
            # Fallback: deterministic pseudo-embedding for dev/test
            vector = self._fallback_embed(text)

        return EmbeddingResult(
            text=text,
            vector=vector,
            model=self.model_id,
            dimensions=len(vector),
        )

    async def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        """Generate embeddings for a batch of texts."""
        return [await self.embed(text) for text in texts]

    def _fallback_embed(self, text: str) -> list[float]:
        """Deterministic hash-based pseudo-embedding for testing."""
        rng = np.random.default_rng(seed=hash(text) % (2**32))
        vector = rng.standard_normal(self.dimensions).tolist()
        # Normalize
        norm = float(np.linalg.norm(vector))
        if norm > 0:
            vector = [v / norm for v in vector]
        return vector
