"""Embedding service for NeedNow AI.

Generates vector embeddings for products and text using
sentence-transformers (all-MiniLM-L6-v2). Supports single-text,
single-product, and batch-product operations.

Architecture:
    - Model: all-MiniLM-L6-v2 (384 dimensions, fast inference)
    - Combines title + description + features + categories for products
    - Thread-safe singleton model loading
    - Batch processing for throughput
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class EmbeddingServiceError(Exception):
    """Raised when embedding generation fails."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


# ---------------------------------------------------------------------------
# Embedding Service
# ---------------------------------------------------------------------------


class EmbeddingService:
    """Generates vector embeddings using sentence-transformers.

    Uses all-MiniLM-L6-v2 (384-dimensional vectors) for fast,
    high-quality semantic embeddings of product and query text.

    Args:
        model_name: HuggingFace model identifier.
        device: Compute device ("cpu", "cuda", or None for auto).
    """

    MODEL_NAME = "all-MiniLM-L6-v2"
    DIMENSIONS = 384

    def __init__(
        self,
        model_name: str = MODEL_NAME,
        device: str | None = None,
    ) -> None:
        self._model_name = model_name
        self._device = device
        self._model: SentenceTransformer | None = None

        logger.info(
            "EmbeddingService initialized: model=%s, device=%s",
            model_name,
            device or "auto",
        )

    @property
    def model(self) -> SentenceTransformer:
        """Lazy-load the model on first access."""
        if self._model is None:
            logger.info("Loading sentence-transformer model: %s", self._model_name)
            self._model = SentenceTransformer(self._model_name, device=self._device)
            logger.info("Model loaded successfully (dim=%d)", self.DIMENSIONS)
        return self._model

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_text_embedding(self, text: str) -> list[float]:
        """Generate an embedding vector for arbitrary text.

        Args:
            text: Input text string.

        Returns:
            List of floats (384 dimensions).

        Raises:
            EmbeddingServiceError: If embedding generation fails.
        """
        if not text or not text.strip():
            raise EmbeddingServiceError("Cannot generate embedding for empty text")

        try:
            embedding = self.model.encode(
                text,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            return embedding.tolist()

        except Exception as exc:
            logger.error("Failed to generate text embedding: %s", exc)
            raise EmbeddingServiceError(
                f"Text embedding generation failed: {exc}"
            ) from exc

    def generate_product_embedding(
        self, product: dict[str, Any]
    ) -> list[float]:
        """Generate an embedding for a product by combining its fields.

        Combines title, description, features, and categories into a
        single text representation before encoding.

        Args:
            product: Dict with product fields (title, description,
                features, categories).

        Returns:
            List of floats (384 dimensions).

        Raises:
            EmbeddingServiceError: If the product has no embeddable content.
        """
        text = self._build_product_text(product)

        if not text.strip():
            raise EmbeddingServiceError(
                f"Product has no embeddable content: {product.get('title', 'unknown')}"
            )

        return self.generate_text_embedding(text)

    def batch_generate_embeddings(
        self,
        products: list[dict[str, Any]],
        *,
        batch_size: int = 64,
        show_progress: bool = False,
    ) -> list[list[float] | None]:
        """Generate embeddings for a batch of products.

        Products that fail to produce embeddable text are returned as None
        in the output list (positional correspondence maintained).

        Args:
            products: List of product dicts.
            batch_size: Encoding batch size for the model.
            show_progress: Whether to show a progress bar.

        Returns:
            List of embedding vectors (or None for skipped products).
            Same length and order as input.

        Raises:
            EmbeddingServiceError: If the batch encoding itself fails.
        """
        if not products:
            return []

        # Build text representations
        texts: list[str] = []
        valid_indices: list[int] = []
        results: list[list[float] | None] = [None] * len(products)

        for idx, product in enumerate(products):
            try:
                text = self._build_product_text(product)
                if text.strip():
                    texts.append(text)
                    valid_indices.append(idx)
                else:
                    logger.debug(
                        "Skipping product %d: no embeddable content", idx
                    )
            except Exception as exc:
                logger.warning(
                    "Skipping product %d: text extraction failed — %s", idx, exc
                )

        if not texts:
            logger.warning("No valid texts in batch of %d products", len(products))
            return results

        # Batch encode
        try:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                normalize_embeddings=True,
                show_progress_bar=show_progress,
            )

            for i, idx in enumerate(valid_indices):
                results[idx] = embeddings[i].tolist()

            logger.debug(
                "Batch embedding complete: %d/%d products encoded",
                len(valid_indices),
                len(products),
            )

        except Exception as exc:
            logger.error("Batch embedding failed: %s", exc)
            raise EmbeddingServiceError(
                f"Batch embedding generation failed: {exc}"
            ) from exc

        return results

    # ------------------------------------------------------------------
    # Private Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_product_text(product: dict[str, Any]) -> str:
        """Build a combined text representation from product fields.

        Combines: title + description + features + categories
        into a single string optimized for semantic embedding.

        Args:
            product: Product dict with optional fields.

        Returns:
            Combined text string.
        """
        parts: list[str] = []

        # Title (highest signal)
        title = product.get("title", "")
        if isinstance(title, str) and title.strip():
            parts.append(title.strip())

        # Description
        description = product.get("description", "")
        if isinstance(description, list):
            desc_text = " ".join(str(d) for d in description if d)
        elif isinstance(description, str):
            desc_text = description
        else:
            desc_text = ""
        if desc_text.strip():
            parts.append(desc_text.strip())

        # Features
        features = product.get("features", [])
        if isinstance(features, list) and features:
            features_text = ". ".join(str(f) for f in features if f)
            if features_text.strip():
                parts.append(features_text.strip())

        # Categories
        categories = product.get("categories", [])
        if isinstance(categories, list) and categories:
            # Flatten nested category lists
            flat_cats: list[str] = []
            for cat in categories:
                if isinstance(cat, list):
                    flat_cats.extend(str(c) for c in cat if c)
                elif isinstance(cat, str) and cat:
                    flat_cats.append(cat)
            if flat_cats:
                parts.append(", ".join(flat_cats))

        # Also include main_category if present
        main_cat = product.get("main_category", "")
        if isinstance(main_cat, str) and main_cat.strip():
            if main_cat.strip() not in " ".join(parts):
                parts.append(main_cat.strip())

        return " | ".join(parts)
