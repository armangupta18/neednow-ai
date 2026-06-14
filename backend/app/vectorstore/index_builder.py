"""Index builder module for NeedNow AI.

Builds and manages FAISS indexes from product catalog and user memory
embeddings. Handles vector validation, index construction, rebuild
workflows, and post-build optimization.

Future compatibility:
    - Amazon Product Dataset (large-scale catalog ingestion)
    - User Memory Dataset (preference/purchase/behavior vectors)
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable

import numpy as np

from app.vectorstore.faiss_manager import FAISSManager, FAISSManagerError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class IndexBuilderError(Exception):
    """Base exception for index building operations."""


class VectorValidationError(IndexBuilderError):
    """Raised when vector validation fails."""


# ---------------------------------------------------------------------------
# Result Models
# ---------------------------------------------------------------------------


@dataclass
class ValidationReport:
    """Report from vector validation."""

    total_vectors: int = 0
    valid_vectors: int = 0
    invalid_vectors: int = 0
    issues: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return self.invalid_vectors == 0


@dataclass
class IndexBuildResult:
    """Summary of an index build operation."""

    index_name: str
    vectors_added: int = 0
    vectors_skipped: int = 0
    dimensions: int = 0
    build_time_ms: float = 0.0
    success: bool = True
    error: str | None = None
    validation_report: ValidationReport | None = None


# ---------------------------------------------------------------------------
# Type Aliases
# ---------------------------------------------------------------------------

EmbedFn = Callable[[str], Awaitable[list[float]]]


# ---------------------------------------------------------------------------
# IndexBuilder
# ---------------------------------------------------------------------------


class IndexBuilder:
    """Builds FAISS indexes from product and memory embeddings.

    Coordinates embedding generation, vector validation, index construction,
    and optimization. Designed for batch operations during data ingestion
    and periodic index rebuilds.

    Args:
        faiss_manager: FAISSManager for index lifecycle operations.
        embed_fn: Async callable that converts text to a vector.
        dimensions: Expected vector dimensionality (used for validation).
        batch_size: Number of vectors to process per insertion batch.
    """

    # Default index names for domain-specific indexes
    PRODUCT_INDEX = "products"
    MEMORY_INDEX = "user_memory"

    def __init__(
        self,
        faiss_manager: FAISSManager,
        embed_fn: EmbedFn | None = None,
        dimensions: int | None = None,
        batch_size: int = 500,
    ) -> None:
        self.faiss_manager = faiss_manager
        self._embed_fn = embed_fn
        self.dimensions = dimensions or faiss_manager.dimensions
        self.batch_size = batch_size

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def build_product_index(
        self,
        products: list[dict[str, Any]],
        *,
        index_name: str | None = None,
        id_field: str = "asin",
        text_field: str = "title",
        metadata_fields: list[str] | None = None,
        overwrite: bool = False,
        validate: bool = True,
    ) -> IndexBuildResult:
        """Build a FAISS index from Amazon product data.

        Designed for compatibility with the Amazon Product Dataset schema:
        each product dict should contain at minimum an ID field and a text
        field for embedding generation.

        Args:
            products: List of product dicts from the catalog.
            index_name: Index name override (defaults to "products").
            id_field: Key for product ID (default "asin" for Amazon datasets).
            text_field: Key for the text to embed (default "title").
            metadata_fields: Additional keys to store alongside vectors.
            overwrite: Whether to replace an existing index.
            validate: Whether to validate vectors before insertion.

        Returns:
            IndexBuildResult with build stats and any validation issues.
        """
        name = index_name or self.PRODUCT_INDEX
        default_meta = metadata_fields or ["title", "category", "brand", "price"]

        logger.info(
            "Building product index '%s' from %d products", name, len(products)
        )

        return await self._build_index_from_documents(
            index_name=name,
            documents=products,
            id_field=id_field,
            text_field=text_field,
            metadata_fields=default_meta,
            overwrite=overwrite,
            validate=validate,
        )

    async def build_memory_index(
        self,
        memories: list[dict[str, Any]],
        *,
        index_name: str | None = None,
        id_field: str = "memory_id",
        text_field: str = "content",
        metadata_fields: list[str] | None = None,
        overwrite: bool = False,
        validate: bool = True,
    ) -> IndexBuildResult:
        """Build a FAISS index from user memory embeddings.

        Supports preference, purchase, and behavior memory datasets.
        Each memory dict should contain a unique ID and text content.

        Args:
            memories: List of memory dicts.
            index_name: Index name override (defaults to "user_memory").
            id_field: Key for memory ID.
            text_field: Key for memory text content.
            metadata_fields: Additional keys to retain.
            overwrite: Whether to replace an existing index.
            validate: Whether to validate vectors before insertion.

        Returns:
            IndexBuildResult with build stats.
        """
        name = index_name or self.MEMORY_INDEX
        default_meta = metadata_fields or ["memory_type", "user_id", "created_at"]

        logger.info(
            "Building memory index '%s' from %d memories", name, len(memories)
        )

        return await self._build_index_from_documents(
            index_name=name,
            documents=memories,
            id_field=id_field,
            text_field=text_field,
            metadata_fields=default_meta,
            overwrite=overwrite,
            validate=validate,
        )

    async def rebuild_index(
        self,
        index_name: str,
        documents: list[dict[str, Any]],
        *,
        id_field: str = "id",
        text_field: str = "text",
        metadata_fields: list[str] | None = None,
        validate: bool = True,
    ) -> IndexBuildResult:
        """Rebuild an existing index from scratch.

        Drops the current index and reconstructs it from the provided
        document set. Use for periodic maintenance or after significant
        data changes.

        Args:
            index_name: Target index to rebuild.
            documents: Complete replacement document set.
            id_field: Key for document ID.
            text_field: Key for text content.
            metadata_fields: Additional metadata keys.
            validate: Whether to validate vectors.

        Returns:
            IndexBuildResult for the fresh build.
        """
        logger.info(
            "Rebuilding index '%s' with %d documents", index_name, len(documents)
        )

        return await self._build_index_from_documents(
            index_name=index_name,
            documents=documents,
            id_field=id_field,
            text_field=text_field,
            metadata_fields=metadata_fields or [],
            overwrite=True,
            validate=validate,
        )

    async def validate_vectors(
        self,
        vectors: list[list[float]],
        *,
        ids: list[str] | None = None,
    ) -> ValidationReport:
        """Validate a batch of vectors for correctness.

        Checks:
            - Correct dimensionality
            - No NaN or Inf values
            - Non-zero magnitude (zero vectors are not useful)
            - Finite value range

        Args:
            vectors: List of vectors to validate.
            ids: Optional IDs for error reporting.

        Returns:
            ValidationReport with detailed issue descriptions.
        """
        report = ValidationReport(total_vectors=len(vectors))
        labels = ids or [str(i) for i in range(len(vectors))]

        for idx, (vector, label) in enumerate(zip(vectors, labels)):
            issues = self._validate_single_vector(vector, label)
            if issues:
                report.invalid_vectors += 1
                report.issues.extend(issues)
            else:
                report.valid_vectors += 1

        if report.is_valid:
            logger.debug("Validation passed: %d vectors OK", report.total_vectors)
        else:
            logger.warning(
                "Validation found %d invalid vectors out of %d",
                report.invalid_vectors,
                report.total_vectors,
            )

        return report

    # ------------------------------------------------------------------
    # Private Implementation
    # ------------------------------------------------------------------

    async def _build_index_from_documents(
        self,
        *,
        index_name: str,
        documents: list[dict[str, Any]],
        id_field: str,
        text_field: str,
        metadata_fields: list[str],
        overwrite: bool,
        validate: bool,
    ) -> IndexBuildResult:
        """Core index-building logic shared by all public build methods."""
        start = time.perf_counter()

        try:
            # Create or overwrite the index
            await self.faiss_manager.create_index(index_name, overwrite=overwrite)

            # Generate embeddings
            ids: list[str] = []
            vectors: list[list[float]] = []
            metadata_list: list[dict[str, Any]] = []
            skipped = 0

            for doc in documents:
                doc_id = str(doc.get(id_field, ""))
                text = doc.get(text_field, "")

                if not doc_id:
                    logger.warning("Skipping document without ID field '%s'", id_field)
                    skipped += 1
                    continue

                if not text:
                    logger.debug("Skipping %s: empty text field '%s'", doc_id, text_field)
                    skipped += 1
                    continue

                vector = await self._generate_embedding(text)
                meta = {f: doc[f] for f in metadata_fields if f in doc}

                ids.append(doc_id)
                vectors.append(vector)
                metadata_list.append(meta)

            # Validate vectors if requested
            validation_report: ValidationReport | None = None
            if validate and vectors:
                validation_report = await self.validate_vectors(vectors, ids=ids)
                if not validation_report.is_valid:
                    # Filter out invalid vectors
                    valid_ids, valid_vectors, valid_meta = self._filter_valid_vectors(
                        ids, vectors, metadata_list
                    )
                    skipped += len(ids) - len(valid_ids)
                    ids, vectors, metadata_list = valid_ids, valid_vectors, valid_meta

            # Insert in batches
            added = 0
            for batch_start in range(0, len(ids), self.batch_size):
                batch_end = batch_start + self.batch_size
                batch_ids = ids[batch_start:batch_end]
                batch_vectors = vectors[batch_start:batch_end]
                batch_meta = metadata_list[batch_start:batch_end]

                added += await self.faiss_manager.add_vectors(
                    index_name, batch_ids, batch_vectors, batch_meta
                )

            # Optimize index after build
            await self._optimize_index(index_name)

            elapsed_ms = (time.perf_counter() - start) * 1000

            logger.info(
                "Index '%s' built: %d vectors added, %d skipped (%.1fms)",
                index_name,
                added,
                skipped,
                elapsed_ms,
            )

            return IndexBuildResult(
                index_name=index_name,
                vectors_added=added,
                vectors_skipped=skipped,
                dimensions=self.dimensions,
                build_time_ms=elapsed_ms,
                success=True,
                validation_report=validation_report,
            )

        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.error(
                "Failed to build index '%s': %s (%.1fms)",
                index_name,
                exc,
                elapsed_ms,
            )
            return IndexBuildResult(
                index_name=index_name,
                dimensions=self.dimensions,
                build_time_ms=elapsed_ms,
                success=False,
                error=str(exc),
            )

    async def _generate_embedding(self, text: str) -> list[float]:
        """Generate an embedding vector using the configured function."""
        if self._embed_fn is not None:
            return await self._embed_fn(text)
        raise IndexBuilderError(
            "No embed_fn provided to IndexBuilder. "
            "Pass an async embedding function at initialization."
        )

    async def _optimize_index(self, index_name: str) -> None:
        """Post-build index optimization.

        For flat indexes this is a no-op; for IVF/HNSW indexes this
        would trigger training or graph construction. Placeholder for
        future scaling needs.
        """
        stats = await self.faiss_manager.get_index_stats(index_name)
        total = stats.get("total_vectors", 0)

        if total > 100_000:
            logger.info(
                "Index '%s' has %d vectors — consider upgrading to IVF index "
                "for better search performance at scale.",
                index_name,
                total,
            )

    def _validate_single_vector(
        self, vector: list[float], label: str
    ) -> list[str]:
        """Validate a single vector and return a list of issues (empty = valid)."""
        issues: list[str] = []

        # Dimension check
        if len(vector) != self.dimensions:
            issues.append(
                f"[{label}] Dimension mismatch: expected {self.dimensions}, got {len(vector)}"
            )
            return issues  # Skip further checks if dimensions wrong

        arr = np.array(vector, dtype=np.float32)

        # NaN check
        if np.any(np.isnan(arr)):
            issues.append(f"[{label}] Contains NaN values")

        # Inf check
        if np.any(np.isinf(arr)):
            issues.append(f"[{label}] Contains Inf values")

        # Zero-magnitude check
        magnitude = float(np.linalg.norm(arr))
        if magnitude == 0.0:
            issues.append(f"[{label}] Zero-magnitude vector (no information)")

        # Extreme value check
        max_abs = float(np.max(np.abs(arr)))
        if max_abs > 1e6:
            issues.append(
                f"[{label}] Contains extreme values (max abs: {max_abs:.2e})"
            )

        return issues

    def _filter_valid_vectors(
        self,
        ids: list[str],
        vectors: list[list[float]],
        metadata_list: list[dict[str, Any]],
    ) -> tuple[list[str], list[list[float]], list[dict[str, Any]]]:
        """Remove invalid vectors from the batch."""
        valid_ids: list[str] = []
        valid_vectors: list[list[float]] = []
        valid_meta: list[dict[str, Any]] = []

        for doc_id, vector, meta in zip(ids, vectors, metadata_list):
            issues = self._validate_single_vector(vector, doc_id)
            if not issues:
                valid_ids.append(doc_id)
                valid_vectors.append(vector)
                valid_meta.append(meta)

        return valid_ids, valid_vectors, valid_meta
