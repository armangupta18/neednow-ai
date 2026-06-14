"""Generate sustainability scores from PostgreSQL products.

Reads all products from the database, computes sustainability scores
across 5 dimensions, and saves to datasets/sustainability/sustainability_scores.json.

Usage:
    python scripts/generate_sustainability_scores.py
    python scripts/generate_sustainability_scores.py --batch-size 1000
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
from app.services.sustainability_scorer import SustainabilityScorerService


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_BATCH_SIZE = 1000
DEFAULT_OUTPUT = "datasets/sustainability/sustainability_scores.json"
LOG_INTERVAL = 1000


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def main(batch_size: int, output_path: str) -> None:
    """Generate sustainability scores for all products in PostgreSQL."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    logger = logging.getLogger("sustainability_scores")

    logger.info("=" * 65)
    logger.info("  NeedNow AI — Sustainability Score Generation (from DB)")
    logger.info("=" * 65)

    # Initialize scorer
    scorer = SustainabilityScorerService(scores_path=output_path)

    # Get total product count
    async with AsyncSessionLocal() as session:
        count_result = await session.execute(
            select(func.count()).select_from(Product)
        )
        total_products = count_result.scalar_one()

    logger.info("Products in PostgreSQL: %d", total_products)
    logger.info("Batch size: %d", batch_size)
    logger.info("Output: %s", output_path)
    logger.info("-" * 65)

    # Statistics
    total_processed = 0
    total_scored = 0
    total_skipped = 0
    high_scores = 0
    start_time = time.perf_counter()

    # Process in batches
    offset = 0

    while offset < total_products:
        async with AsyncSessionLocal() as session:
            stmt = (
                select(Product)
                .order_by(Product.id)
                .offset(offset)
                .limit(batch_size)
            )
            result = await session.execute(stmt)
            products = list(result.scalars().all())

        if not products:
            break

        for product in products:
            total_processed += 1

            # Build product dict for scoring
            title = product.title or ""
            if not title.strip():
                total_skipped += 1
                continue

            product_dict = {
                "parent_asin": str(product.id),
                "title": title,
                "description": product.description or "",
                "features": [],
                "categories": [product.category] if product.category else [],
            }

            try:
                score = scorer.score_product(product_dict)
                total_scored += 1

                if score.overall_score >= 50.0:
                    high_scores += 1

            except Exception as exc:
                total_skipped += 1
                if total_skipped <= 5:
                    logger.warning(
                        "Scoring failed for product %s: %s", product.id, exc
                    )

        # Log progress
        if total_processed % LOG_INTERVAL == 0 or offset + batch_size >= total_products:
            elapsed = time.perf_counter() - start_time
            rate = total_processed / elapsed if elapsed > 0 else 0
            pct = (total_processed / total_products) * 100 if total_products else 0
            logger.info(
                "[%.1f%%] processed=%d/%d | scored=%d | skipped=%d | high(≥50)=%d | %.0f/sec",
                pct, total_processed, total_products, total_scored, total_skipped, high_scores, rate,
            )

        offset += batch_size

    # Save scores to JSON
    scorer.save_scores()

    # Final statistics
    elapsed = time.perf_counter() - start_time

    logger.info("-" * 65)
    logger.info("SUSTAINABILITY SCORING COMPLETE")
    logger.info("-" * 65)
    logger.info("  Total processed:        %d", total_processed)
    logger.info("  Total scored:           %d", total_scored)
    logger.info("  Total skipped:          %d", total_skipped)
    logger.info("  High sustainability:    %d (≥50 overall)", high_scores)
    logger.info("  Duration:               %.1f seconds", elapsed)
    logger.info("  Output:                 %s", output_path)
    logger.info("  Scores in store:        %d", scorer.count())
    logger.info("=" * 65)

    # Print summary
    print(f"\n{'=' * 55}")
    print(f"  ✅ Sustainability Score Generation Complete")
    print(f"{'─' * 55}")
    print(f"  Processed:        {total_processed:,}")
    print(f"  Scored:           {total_scored:,}")
    print(f"  Skipped:          {total_skipped:,}")
    print(f"  High scores:      {high_scores:,} (≥50)")
    print(f"  Duration:         {elapsed:.1f}s")
    print(f"  Output:           {output_path}")
    print(f"{'=' * 55}\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate sustainability scores from PostgreSQL products."
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"DB page fetch size (default: {DEFAULT_BATCH_SIZE})",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=DEFAULT_OUTPUT,
        help=f"Output JSON path (default: {DEFAULT_OUTPUT})",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main(args.batch_size, args.output))
