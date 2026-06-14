"""Product ingestion script for NeedNow AI.

Loads Amazon product data from JSONL files into PostgreSQL.
Supports any Amazon category dataset — just pass the file path.

Usage:
    python scripts/load_products.py
    python scripts/load_products.py --file datasets/products/meta_Electronics.jsonl
    python scripts/load_products.py --file datasets/products/meta_Health_and_Personal_Care.jsonl --batch-size 1000
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

from app.database.connection import AsyncSessionLocal, init_db
from app.services.data_ingestion import DataIngestionService


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_DATASET = "datasets/products/meta_Health_and_Personal_Care.jsonl"
DEFAULT_BATCH_SIZE = 500
DEFAULT_LOG_INTERVAL = 1000


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def main(
    file_path: str,
    batch_size: int,
    log_interval: int,
) -> None:
    """Run the product ingestion pipeline."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    logger = logging.getLogger("load_products")

    path = Path(file_path)
    if not path.exists():
        logger.error("File not found: %s", path)
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("NeedNow AI — Product Data Ingestion")
    logger.info("=" * 60)
    logger.info("File: %s", path)
    logger.info("Batch size: %d", batch_size)
    logger.info("Log interval: %d", log_interval)
    logger.info("-" * 60)

    # Initialize database tables
    logger.info("Initializing database tables...")
    await init_db()

    # Run ingestion
    start_time = time.perf_counter()

    async with AsyncSessionLocal() as session:
        service = DataIngestionService(
            session=session,
            batch_size=batch_size,
            log_interval=log_interval,
        )
        result = await service.ingest_file(path)

    elapsed = time.perf_counter() - start_time

    # Print summary
    logger.info("-" * 60)
    logger.info("INGESTION COMPLETE")
    logger.info("-" * 60)
    logger.info("Total processed:  %d", result.total_processed)
    logger.info("Total inserted:   %d", result.total_inserted)
    logger.info("Total skipped:    %d", result.total_skipped)
    logger.info("Duration:         %.2f seconds", elapsed)

    if result.total_inserted > 0:
        rate = result.total_inserted / elapsed
        logger.info("Insert rate:      %.0f records/sec", rate)

    if result.errors:
        logger.warning("Errors encountered: %d", len(result.errors))
        for err in result.errors[:10]:
            logger.warning("  %s", err)
        if len(result.errors) > 10:
            logger.warning("  ... and %d more", len(result.errors) - 10)

    logger.info("=" * 60)

    # Print to stdout for CI/CD pipelines
    print(f"\n{'=' * 50}")
    print(f"  Total processed: {result.total_processed}")
    print(f"  Total inserted:  {result.total_inserted}")
    print(f"  Total skipped:   {result.total_skipped}")
    print(f"  Duration:        {elapsed:.2f}s")
    print(f"{'=' * 50}\n")


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load Amazon product data into NeedNow AI database."
    )
    parser.add_argument(
        "--file",
        type=str,
        default=DEFAULT_DATASET,
        help=f"Path to JSONL dataset (default: {DEFAULT_DATASET})",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Records per insert batch (default: {DEFAULT_BATCH_SIZE})",
    )
    parser.add_argument(
        "--log-interval",
        type=int,
        default=DEFAULT_LOG_INTERVAL,
        help=f"Log progress every N records (default: {DEFAULT_LOG_INTERVAL})",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main(args.file, args.batch_size, args.log_interval))
