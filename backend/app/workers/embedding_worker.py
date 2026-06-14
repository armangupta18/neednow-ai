"""Embedding worker for NeedNow AI.

Generates and updates embeddings for products and user memories,
keeping FAISS vector indexes synchronized with the data layer.

Architecture:
    - Embedder: Converts text to vector representations.
    - TextChunker: Splits long text into embeddable chunks.
    - FAISSManager: Manages vector index storage and retrieval.

Dependencies:
    - app.memory.embeddings.embedder.Embedder
    - app.memory.embeddings.chunker.TextChunker
    - app.vectorstore.faiss_manager.FAISSManager
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.memory.embeddings.chunker import TextChunker
from app.memory.embeddings.embedder import Embedder, EmbeddingResult
from app.vectorstore.faiss_manager import FAISSManager

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class EmbeddingWorkerError(Exception):
    """Base exception for embedding worker operations."""


class EmbeddingGenerationError(EmbeddingWorkerError):
    """Raised when embedding generation fails for a document."""


class IndexUpdateError(EmbeddingWorkerError):
    """Raised when the FAISS index update fails."""


# ---------------------------------------------------------------------------
# Result Models
# ---------------------------------------------------------------------------


@dataclass
class EmbeddingJob:
    """A single embedding job to process."""

    id: str
    text: str
    index_name: str
    metadata: dict[str, Any] = field(default_factory=dict)
    retries: int = 0


@dataclass
class EmbeddingJobResult:
    """Result of processing a single embedding job."""

    job_id: str
    success: bool = True
    chunks_generated: int = 0
    vectors_indexed: int = 0
    error: str | None = None


@dataclass
class EmbeddingCycleResult:
    """Summary of a full embedding processing cycle."""

    status: str = "completed"
    products_processed: int = 0
    memories_processed: int = 0
    total_chunks: int = 0
    total_vectors_indexed: int = 0
    failed_jobs: int = 0
    retried_jobs: int = 0
    duration_ms: float = 0.0
    errors: list[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None


# ---------------------------------------------------------------------------
# Worker
# ---------------------------------------------------------------------------


class EmbeddingWorker:
    """Background worker that generates embeddings and updates FAISS indexes.

    Responsibilities:
        - Generate embeddings for new/updated products and memories.
        - Chunk long text before embedding for better retrieval.
        - Update FAISS vector indexes with new embeddings.
        - Retry failed embedding jobs with exponential backoff.
        - Batch processing for throughput efficiency.

    Designed for use with FastAPI BackgroundTasks, APScheduler, or arq.

    Args:
        embedder: Embedder instance for vector generation.
        chunker: TextChunker for splitting long documents.
        faiss_manager: FAISSManager for vector index operations.
        poll_interval_seconds: Seconds between processing cycles.
        batch_size: Max documents to process per cycle.
        max_retries: Max retries for failed embedding jobs.
        chunk_long_text: Whether to chunk text exceeding chunk_threshold chars.
        chunk_threshold: Character count above which text is chunked.
    """

    PRODUCT_INDEX = "products"
    MEMORY_INDEX = "user_memory"

    def __init__(
        self,
        embedder: Embedder,
        chunker: TextChunker,
        faiss_manager: FAISSManager,
        *,
        poll_interval_seconds: float = 60.0,
        batch_size: int = 100,
        max_retries: int = 3,
        chunk_long_text: bool = True,
        chunk_threshold: int = 512,
    ) -> None:
        self.embedder = embedder
        self.chunker = chunker
        self.faiss_manager = faiss_manager
        self.poll_interval_seconds = poll_interval_seconds
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.chunk_long_text = chunk_long_text
        self.chunk_threshold = chunk_threshold

        self._running = False
        self._task: asyncio.Task[None] | None = None
        self._pending_queue: asyncio.Queue[EmbeddingJob] = asyncio.Queue()
        self._retry_queue: list[EmbeddingJob] = []
        self._total_processed = 0
        self._total_failed = 0
        self._last_cycle_result: EmbeddingCycleResult | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Start the background embedding loop."""
        if self._running:
            logger.warning("EmbeddingWorker is already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(
            "EmbeddingWorker started (interval=%ds, batch=%d, max_retries=%d)",
            self.poll_interval_seconds,
            self.batch_size,
            self.max_retries,
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
            "EmbeddingWorker stopped (processed=%d, failed=%d)",
            self._total_processed,
            self._total_failed,
        )

    async def run(self) -> EmbeddingCycleResult:
        """Execute a single full embedding cycle.

        Processes pending product and memory embedding jobs,
        retries failed jobs, and updates FAISS indexes.

        Returns:
            EmbeddingCycleResult with detailed metrics.
        """
        start = time.perf_counter()
        result = EmbeddingCycleResult()

        logger.info("Embedding cycle starting")

        try:
            # Process product embeddings
            product_results = await self.process_product_embeddings()
            result.products_processed = sum(
                1 for r in product_results if r.success
            )
            result.total_chunks += sum(r.chunks_generated for r in product_results)
            result.total_vectors_indexed += sum(
                r.vectors_indexed for r in product_results
            )

            # Process memory embeddings
            memory_results = await self.process_memory_embeddings()
            result.memories_processed = sum(
                1 for r in memory_results if r.success
            )
            result.total_chunks += sum(r.chunks_generated for r in memory_results)
            result.total_vectors_indexed += sum(
                r.vectors_indexed for r in memory_results
            )

            # Retry failed jobs
            retried = await self._process_retry_queue()
            result.retried_jobs = retried

            # Collect errors
            all_results = product_results + memory_results
            for r in all_results:
                if not r.success and r.error:
                    result.errors.append(f"job={r.job_id}: {r.error}")
                    result.failed_jobs += 1

            # Finalize
            result.duration_ms = (time.perf_counter() - start) * 1000
            result.completed_at = datetime.now(timezone.utc)
            result.status = "completed" if not result.errors else "completed_with_errors"

            self._total_processed += result.products_processed + result.memories_processed
            self._total_failed += result.failed_jobs
            self._last_cycle_result = result

            logger.info(
                "Embedding cycle completed: products=%d, memories=%d, chunks=%d, "
                "vectors=%d, failed=%d, retried=%d (%.1fms)",
                result.products_processed,
                result.memories_processed,
                result.total_chunks,
                result.total_vectors_indexed,
                result.failed_jobs,
                result.retried_jobs,
                result.duration_ms,
            )

        except Exception as exc:
            result.status = "failed"
            result.errors.append(str(exc))
            result.duration_ms = (time.perf_counter() - start) * 1000
            result.completed_at = datetime.now(timezone.utc)
            self._total_failed += 1
            logger.error("Embedding cycle failed: %s", exc)

        return result

    # ------------------------------------------------------------------
    # Public Processing Methods
    # ------------------------------------------------------------------

    async def process_product_embeddings(
        self,
        products: list[dict[str, Any]] | None = None,
    ) -> list[EmbeddingJobResult]:
        """Generate embeddings for product documents and index them.

        Args:
            products: Optional list of product dicts to embed. If None,
                drains the internal pending queue for product jobs.
                Each dict should have "id" and "title"/"description".

        Returns:
            List of EmbeddingJobResult for each processed product.
        """
        jobs = self._build_product_jobs(products) if products else self._drain_queue(
            self.PRODUCT_INDEX
        )

        if not jobs:
            logger.debug("No product embedding jobs to process")
            return []

        logger.info("Processing %d product embedding jobs", len(jobs))
        return await self._process_jobs(jobs)

    async def process_memory_embeddings(
        self,
        memories: list[dict[str, Any]] | None = None,
    ) -> list[EmbeddingJobResult]:
        """Generate embeddings for user memory documents and index them.

        Args:
            memories: Optional list of memory dicts to embed. If None,
                drains the internal pending queue for memory jobs.
                Each dict should have "memory_id" and "content".

        Returns:
            List of EmbeddingJobResult for each processed memory.
        """
        jobs = self._build_memory_jobs(memories) if memories else self._drain_queue(
            self.MEMORY_INDEX
        )

        if not jobs:
            logger.debug("No memory embedding jobs to process")
            return []

        logger.info("Processing %d memory embedding jobs", len(jobs))
        return await self._process_jobs(jobs)

    async def update_embeddings(
        self,
        documents: list[dict[str, Any]],
        *,
        index_name: str,
        id_field: str = "id",
        text_field: str = "text",
    ) -> EmbeddingCycleResult:
        """Update embeddings for a set of documents in a specified index.

        Removes existing vectors for the given IDs, re-generates
        embeddings, and re-indexes. Useful for handling document updates.

        Args:
            documents: Documents to re-embed.
            index_name: Target FAISS index.
            id_field: Key for document ID.
            text_field: Key for text content to embed.

        Returns:
            EmbeddingCycleResult with metrics.
        """
        start = time.perf_counter()
        result = EmbeddingCycleResult()

        logger.info(
            "Updating embeddings for %d documents in '%s'",
            len(documents),
            index_name,
        )

        try:
            # Remove existing vectors
            doc_ids = [str(doc[id_field]) for doc in documents if doc.get(id_field)]
            if doc_ids:
                await self.faiss_manager.remove_vectors(index_name, doc_ids)

            # Build jobs and process
            jobs: list[EmbeddingJob] = []
            for doc in documents:
                doc_id = str(doc.get(id_field, ""))
                text = doc.get(text_field, "")
                if doc_id and text:
                    meta = {k: v for k, v in doc.items() if k not in (id_field, text_field)}
                    jobs.append(
                        EmbeddingJob(
                            id=doc_id,
                            text=text,
                            index_name=index_name,
                            metadata=meta,
                        )
                    )

            job_results = await self._process_jobs(jobs)

            result.total_vectors_indexed = sum(r.vectors_indexed for r in job_results)
            result.total_chunks = sum(r.chunks_generated for r in job_results)
            result.failed_jobs = sum(1 for r in job_results if not r.success)
            result.duration_ms = (time.perf_counter() - start) * 1000
            result.completed_at = datetime.now(timezone.utc)
            result.status = "completed"

            logger.info(
                "Embedding update completed: vectors=%d, chunks=%d, failed=%d (%.1fms)",
                result.total_vectors_indexed,
                result.total_chunks,
                result.failed_jobs,
                result.duration_ms,
            )

        except Exception as exc:
            result.status = "failed"
            result.errors.append(str(exc))
            result.duration_ms = (time.perf_counter() - start) * 1000
            result.completed_at = datetime.now(timezone.utc)
            logger.error("Embedding update failed: %s", exc)

        return result

    # ------------------------------------------------------------------
    # Queue Management
    # ------------------------------------------------------------------

    async def enqueue(self, job: EmbeddingJob) -> None:
        """Add an embedding job to the pending queue."""
        await self._pending_queue.put(job)
        logger.debug("Enqueued embedding job: id=%s, index=%s", job.id, job.index_name)

    async def enqueue_product(
        self,
        product_id: str,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Convenience method to enqueue a product embedding job."""
        await self.enqueue(
            EmbeddingJob(
                id=product_id,
                text=text,
                index_name=self.PRODUCT_INDEX,
                metadata=metadata or {},
            )
        )

    async def enqueue_memory(
        self,
        memory_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Convenience method to enqueue a memory embedding job."""
        await self.enqueue(
            EmbeddingJob(
                id=memory_id,
                text=content,
                index_name=self.MEMORY_INDEX,
                metadata=metadata or {},
            )
        )

    @property
    def pending_count(self) -> int:
        return self._pending_queue.qsize()

    @property
    def retry_count(self) -> int:
        return len(self._retry_queue)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def total_processed(self) -> int:
        return self._total_processed

    @property
    def total_failed(self) -> int:
        return self._total_failed

    @property
    def last_cycle_result(self) -> EmbeddingCycleResult | None:
        return self._last_cycle_result

    # ------------------------------------------------------------------
    # Private Implementation
    # ------------------------------------------------------------------

    async def _run_loop(self) -> None:
        """Internal loop executing embedding cycles at the configured interval."""
        while self._running:
            try:
                await self.run()
            except Exception as exc:
                logger.error("Unexpected error in embedding loop: %s", exc)
            await asyncio.sleep(self.poll_interval_seconds)

    async def _process_jobs(
        self, jobs: list[EmbeddingJob]
    ) -> list[EmbeddingJobResult]:
        """Process a batch of embedding jobs."""
        results: list[EmbeddingJobResult] = []

        for batch_start in range(0, len(jobs), self.batch_size):
            batch = jobs[batch_start : batch_start + self.batch_size]
            batch_results = await asyncio.gather(
                *[self._process_single_job(job) for job in batch],
                return_exceptions=False,
            )
            results.extend(batch_results)

        return results

    async def _process_single_job(self, job: EmbeddingJob) -> EmbeddingJobResult:
        """Process a single embedding job: chunk → embed → index."""
        result = EmbeddingJobResult(job_id=job.id)

        try:
            # Step 1: Chunk text if it exceeds the threshold
            chunks = self._chunk_text(job.text, job.metadata)
            result.chunks_generated = len(chunks)

            # Step 2: Generate embeddings for each chunk
            ids: list[str] = []
            vectors: list[list[float]] = []
            metadata_list: list[dict[str, Any]] = []

            for i, chunk_text in enumerate(chunks):
                embedding_result: EmbeddingResult = await self.embedder.embed(chunk_text)

                # Use composite ID for multi-chunk documents
                chunk_id = f"{job.id}_chunk_{i}" if len(chunks) > 1 else job.id

                ids.append(chunk_id)
                vectors.append(embedding_result.vector)
                metadata_list.append(
                    {
                        **job.metadata,
                        "source_id": job.id,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                    }
                )

            # Step 3: Index vectors in FAISS
            if ids:
                indexed = await self.faiss_manager.add_vectors(
                    job.index_name, ids, vectors, metadata_list
                )
                result.vectors_indexed = indexed

            logger.debug(
                "Job %s completed: %d chunks, %d vectors indexed",
                job.id,
                result.chunks_generated,
                result.vectors_indexed,
            )

        except Exception as exc:
            result.success = False
            result.error = str(exc)
            logger.warning("Job %s failed: %s", job.id, exc)

            # Add to retry queue if retries remain
            if job.retries < self.max_retries:
                job.retries += 1
                self._retry_queue.append(job)
                logger.debug(
                    "Job %s queued for retry (%d/%d)",
                    job.id,
                    job.retries,
                    self.max_retries,
                )

        return result

    async def _process_retry_queue(self) -> int:
        """Process jobs in the retry queue with exponential backoff."""
        if not self._retry_queue:
            return 0

        retry_jobs = self._retry_queue[:]
        self._retry_queue.clear()

        retried = 0
        for job in retry_jobs:
            # Exponential backoff delay
            delay = 0.5 * (2 ** (job.retries - 1))
            await asyncio.sleep(min(delay, 10.0))

            result = await self._process_single_job(job)
            if result.success:
                retried += 1
                logger.info("Retry succeeded for job %s (attempt %d)", job.id, job.retries)
            # If still failing, _process_single_job will re-add to retry queue
            # if max_retries not exceeded

        return retried

    def _chunk_text(self, text: str, metadata: dict[str, Any]) -> list[str]:
        """Split text into chunks if it exceeds the threshold.

        Returns a list of text strings ready for embedding.
        """
        if not text.strip():
            return []

        if not self.chunk_long_text or len(text) <= self.chunk_threshold:
            return [text]

        # Use TextChunker for long documents
        text_chunks = self.chunker.chunk(
            text,
            metadata={k: str(v) for k, v in metadata.items() if isinstance(v, (str, int, float))},
        )
        return [chunk.text for chunk in text_chunks if chunk.text.strip()]

    def _build_product_jobs(
        self, products: list[dict[str, Any]]
    ) -> list[EmbeddingJob]:
        """Convert product dicts into embedding jobs."""
        jobs: list[EmbeddingJob] = []
        for product in products:
            product_id = str(product.get("id", product.get("asin", "")))
            title = product.get("title", "")
            description = product.get("description", "")
            text = f"{title}. {description}".strip(". ")

            if not product_id or not text:
                continue

            meta = {
                k: v
                for k, v in product.items()
                if k not in ("id", "asin", "title", "description")
                and isinstance(v, (str, int, float, bool))
            }

            jobs.append(
                EmbeddingJob(
                    id=product_id,
                    text=text,
                    index_name=self.PRODUCT_INDEX,
                    metadata=meta,
                )
            )

        return jobs[:self.batch_size]

    def _build_memory_jobs(
        self, memories: list[dict[str, Any]]
    ) -> list[EmbeddingJob]:
        """Convert memory dicts into embedding jobs."""
        jobs: list[EmbeddingJob] = []
        for memory in memories:
            memory_id = str(memory.get("memory_id", memory.get("id", "")))
            content = memory.get("content", "")

            if not memory_id or not content:
                continue

            meta = {
                k: v
                for k, v in memory.items()
                if k not in ("memory_id", "id", "content")
                and isinstance(v, (str, int, float, bool))
            }

            jobs.append(
                EmbeddingJob(
                    id=memory_id,
                    text=content,
                    index_name=self.MEMORY_INDEX,
                    metadata=meta,
                )
            )

        return jobs[:self.batch_size]

    def _drain_queue(self, index_name: str) -> list[EmbeddingJob]:
        """Drain pending jobs from the queue for a given index."""
        jobs: list[EmbeddingJob] = []
        drained = 0

        while not self._pending_queue.empty() and drained < self.batch_size:
            try:
                job = self._pending_queue.get_nowait()
                if job.index_name == index_name:
                    jobs.append(job)
                    drained += 1
                else:
                    # Put back jobs for other indexes
                    self._pending_queue.put_nowait(job)
            except asyncio.QueueEmpty:
                break

        return jobs
