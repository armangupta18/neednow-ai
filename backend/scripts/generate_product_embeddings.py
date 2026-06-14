"""Generate product embeddings and store in ChromaDB.

Reads 60k+ products from PostgreSQL, generates embeddings using
sentence-transformers (all-MiniLM-L6-v2), and indexes them in
ChromaDB persistent storage.

Optimized for large-scale processing:
    - Large DB page fetches (1000 records)
    - Batch encoding (256 at a time for GPU/CPU throughput)
    - Resume support (skips already-indexed products)
    - Progress logging every 500 products

Usage:
    python scripts/generate_product_embeddings.py
    python scripts/generate_product_embeddings.py --batch-size 256 --db-fetch-size 1000
    python scripts/generate_product_embeddings.py --resume  # Skip already indexed
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select, func

from app.database.connection import AsyncSessionLocal
from app.models.product import Product
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore


# ---------------------------------------------------------------------------
# Configuration (optimized for 60k+ products)
# ---------------------------------------------------------------------------

DEFAULT_BATCH_SIZE = 256
DEFAULT_DB_FETCH_SIZE = 1000
LOG_INTERVAL = 500


# ---------------------------------------------------------------------------
# Main Pipeline
# ---------------------------------------------------------------------------


async def generate_embeddings(
    batch_size: int = DEFAULT_BATCH_SIZE,
    db_fetch_size: int = DEFAULT_DB_FETCH_SIZE,
    resume: bool = False,
) -> None:
    """Read products from DB, generate embeddings, store in ChromaDB."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    logger = logging.getLogger("generate_embeddings")

    logger.info("=" * 65)
    logger.info("  NeedNow AI — Product Embedding Generation Pipeline")
    logger.info("=" * 65)

    # Initialize services
    logger.info("Loading embedding model (all-MiniLM-L6-v2)...")
    embedding_service = EmbeddingService()
    # Force model load upfront
    _ = embedding_service.model
    logger.info("Model loaded: %d dimensions", EmbeddingService.DIMENSIONS)

    logger.info("Initializing ChromaDB vector store...")
    vector_store = VectorStore()
    existing_count = vector_store.count()
    logger.info("Existing vectors in store: %d", existing_count)

    # Statistics
    total_processed = 0
    total_indexed = 0
    total_skipped = 0
    total_failed = 0
    start_time = time.perf_counter()

    # Get total product count
    async with AsyncSessionLocal() as session:
        count_result = await session.execute(
            select(func.count()).select_from(Product)
        )
        total_products = count_result.scalar_one()

    logger.info("Products in PostgreSQL: %d", total_products)
    logger.info("Batch size: %d (model), DB fetch: %d, Resume: %s", batch_size, db_fetch_size, resume)
    logger.info("-" * 65)

    # Process in DB pages
    offset = 0

    while offset < total_products:
        # Fetch a page of products
        async with AsyncSessionLocal() as session:
            stmt = (
                select(Product)
                .order_by(Product.id)
                .offset(offset)
                .limit(db_fetch_size)
            )
            result = await session.execute(stmt)
            products = list(result.scalars().all())

        if not products:
            break

        # Build product dicts and filter already-indexed if resuming
        product_dicts: list[dict] = []
        product_records: list[Product] = []

        for product in products:
            product_id = str(product.id)

            # Skip already-indexed products in resume mode
            if resume and _is_indexed(vector_store, product_id):
                total_skipped += 1
                total_processed += 1
                continue

            product_dicts.append({
                "title": product.title or "",
                "description": product.description or "",
                "features": [],
                "categories": [product.category] if product.category else [],
            })
            product_records.append(product)

        # Process in embedding sub-batches
        for batch_start in range(0, len(product_dicts), batch_size):
            batch_end = min(batch_start + batch_size, len(product_dicts))
            batch_dicts = product_dicts[batch_start:batch_end]
            batch_records = product_records[batch_start:batch_end]

            total_processed += len(batch_dicts)

            # Generate embeddings
            try:
                embeddings = embedding_service.batch_generate_embeddings(
                    batch_dicts, batch_size=batch_size
                )
            except Exception as exc:
                logger.error("Embedding generation failed: %s", exc)
                total_failed += len(batch_dicts)
                continue

            # Collect successful embeddings
            valid_embeddings: list[list[float]] = []
            valid_ids: list[str] = []
            valid_titles: list[str] = []
            valid_categories: list[str] = []
            valid_ratings: list[float] = []

            for i, embedding in enumerate(embeddings):
                if embedding is None:
                    total_failed += 1
                    continue

                product = batch_records[i]
                valid_embeddings.append(embedding)
                valid_ids.append(str(product.id))
                valid_titles.append((product.title or "")[:500])
                valid_categories.append(product.category or "Uncategorized")
                valid_ratings.append(0.0)

            # Index in ChromaDB
            if valid_embeddings:
                try:
                    indexed = vector_store.add_products(
                        embeddings=valid_embeddings,
                        parent_asins=valid_ids,
                        titles=valid_titles,
                        categories=valid_categories,
                        ratings=valid_ratings,
                        batch_size=500,
                    )
                    total_indexed += indexed
                except Exception as exc:
                    logger.error("ChromaDB upsert failed: %s", exc)
                    total_failed += len(valid_embeddings)

        # Log progress
        if total_processed % LOG_INTERVAL < db_fetch_size or offset + db_fetch_size >= total_products:
            elapsed = time.perf_counter() - start_time
            rate = total_processed / elapsed if elapsed > 0 else 0
            pct = (total_processed / total_products) * 100 if total_products else 0
            logger.info(
                "[%.1f%%] processed=%d/%d | indexed=%d | skipped=%d | failed=%d | %.0f prod/sec",
                pct, total_processed, total_products, total_indexed, total_skipped, total_failed, rate,
            )

        offset += db_fetch_size

    # Final verification
    final_count = vector_store.count()
    elapsed = time.perf_counter() - start_time

    logger.info("-" * 65)
    logger.info("EMBEDDING GENERATION COMPLETE")
    logger.info("-" * 65)
    logger.info("  Total processed:    %d", total_processed)
    logger.info("  Total indexed:      %d", total_indexed)
    logger.info("  Total skipped:      %d", total_skipped)
    logger.info("  Total failed:       %d", total_failed)
    logger.info("  Duration:           %.1f seconds (%.1f min)", elapsed, elapsed / 60)
    logger.info("  ChromaDB vectors:   %d", final_count)

    if total_indexed > 0:
        rate = total_indexed / elapsed
        logger.info("  Throughput:         %.0f products/sec", rate)

    logger.info("=" * 65)

    # Print summary
    print(f"\n{'=' * 55}")
    print(f"  ✅ Embedding Generation Complete")
    print(f"{'─' * 55}")
    print(f"  Processed:      {total_processed:,}")
    print(f"  Indexed:        {total_indexed:,}")
    print(f"  Skipped:        {total_skipped:,}")
    print(f"  Failed:         {total_failed:,}")
    print(f"  Duration:       {elapsed:.1f}s ({elapsed/60:.1f} min)")
    print(f"  Vector Store:   {final_count:,} vectors")
    print(f"{'=' * 55}\n")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _is_indexed(store: VectorStore, product_id: str) -> bool:
    """Quick check if a product is already in the vector store."""
    try:
        results = store._collection.get(ids=[product_id], include=[])
        return bool(results and results["ids"])
    except Exception:
        return False


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate product embeddings and store in ChromaDB (60k+ products)."
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Model encoding batch size (default: {DEFAULT_BATCH_SIZE})",
    )
    parser.add_argument(
        "--db-fetch-size",
        type=int,
        default=DEFAULT_DB_FETCH_SIZE,
        help=f"DB page fetch size (default: {DEFAULT_DB_FETCH_SIZE})",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        default=False,
        help="Skip products already in ChromaDB (for interrupted runs)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(generate_embeddings(args.batch_size, args.db_fetch_size, args.resume))
