"""Data ingestion service for NeedNow AI.

Reads Amazon product JSONL datasets and inserts them into PostgreSQL
via SQLAlchemy. Supports any Amazon category without code changes —
just point to the corresponding JSONL file.

Architecture:
    - Line-by-line JSONL streaming (memory efficient for large files).
    - Batch inserts for throughput.
    - Skips malformed/incomplete records gracefully.
    - Logs progress every N records.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result Model
# ---------------------------------------------------------------------------


@dataclass
class IngestionResult:
    """Summary of a data ingestion run."""

    total_processed: int = 0
    total_inserted: int = 0
    total_skipped: int = 0
    errors: list[str] = field(default_factory=list)

    def summary(self) -> str:
        return (
            f"Ingestion complete: "
            f"processed={self.total_processed}, "
            f"inserted={self.total_inserted}, "
            f"skipped={self.total_skipped}"
        )


# ---------------------------------------------------------------------------
# Data Ingestion Service
# ---------------------------------------------------------------------------


class DataIngestionService:
    """Ingests Amazon product data from JSONL files into PostgreSQL.

    Supports any Amazon product category dataset. The JSONL schema is
    auto-mapped to the Product model — no code changes required for
    new categories.

    Args:
        session: SQLAlchemy AsyncSession.
        batch_size: Number of records per database insert batch.
        log_interval: Log progress every N records processed.
    """

    def __init__(
        self,
        session: AsyncSession,
        *,
        batch_size: int = 500,
        log_interval: int = 1000,
    ) -> None:
        self._session = session
        self.batch_size = batch_size
        self.log_interval = log_interval

    async def ingest_file(self, file_path: str | Path) -> IngestionResult:
        """Ingest a JSONL file into the products table.

        Reads the file line-by-line, extracts product fields, and
        inserts in batches. Skips malformed records and logs progress.

        Args:
            file_path: Path to the .jsonl dataset file.

        Returns:
            IngestionResult with counts and any error messages.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Dataset file not found: {path}")

        result = IngestionResult()
        batch: list[Product] = []

        logger.info("Starting ingestion from: %s", path.name)

        with open(path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, start=1):
                result.total_processed += 1

                # Parse JSON line
                record = self._parse_line(line, line_num, result)
                if record is None:
                    continue

                # Map to Product model
                product = self._map_to_product(record, line_num, result)
                if product is None:
                    continue

                batch.append(product)

                # Flush batch when full
                if len(batch) >= self.batch_size:
                    inserted = await self._insert_batch(batch, result)
                    result.total_inserted += inserted
                    batch.clear()

                # Log progress
                if result.total_processed % self.log_interval == 0:
                    logger.info(
                        "Progress: processed=%d, inserted=%d, skipped=%d",
                        result.total_processed,
                        result.total_inserted,
                        result.total_skipped,
                    )

        # Insert remaining records
        if batch:
            inserted = await self._insert_batch(batch, result)
            result.total_inserted += inserted

        logger.info(result.summary())
        return result

    # ------------------------------------------------------------------
    # Private Helpers
    # ------------------------------------------------------------------

    def _parse_line(
        self, line: str, line_num: int, result: IngestionResult
    ) -> dict[str, Any] | None:
        """Parse a single JSONL line. Returns None on failure."""
        try:
            return json.loads(line.strip())
        except (json.JSONDecodeError, ValueError) as exc:
            result.total_skipped += 1
            result.errors.append(f"Line {line_num}: JSON parse error — {exc}")
            return None

    def _map_to_product(
        self, record: dict[str, Any], line_num: int, result: IngestionResult
    ) -> Product | None:
        """Map a JSONL record to a Product model instance. Returns None if invalid."""
        try:
            title = record.get("title", "").strip()
            if not title:
                result.total_skipped += 1
                return None

            # Extract description
            description = self._extract_description(record)

            # Extract category
            category = self._extract_category(record)

            # Extract price
            price = self._extract_price(record)

            # Extract brand/store
            brand = (record.get("store") or "").strip() or None

            return Product(
                title=title[:500],
                description=description,
                category=category[:255] if category else "Uncategorized",
                brand=brand[:255] if brand else None,
                price=price,
                stock=100,  # Default stock for seeded products
            )

        except Exception as exc:
            result.total_skipped += 1
            result.errors.append(f"Line {line_num}: mapping error — {exc}")
            return None

    async def _insert_batch(
        self, batch: list[Product], result: IngestionResult
    ) -> int:
        """Insert a batch of products. Returns count inserted."""
        try:
            self._session.add_all(batch)
            await self._session.commit()
            return len(batch)
        except Exception as exc:
            await self._session.rollback()
            result.errors.append(f"Batch insert failed: {exc}")
            logger.error("Batch insert failed: %s", exc)
            result.total_skipped += len(batch)
            return 0

    @staticmethod
    def _extract_description(record: dict[str, Any]) -> str:
        """Extract description from description field or features list."""
        description = record.get("description", [])

        # description can be a list of strings or a single string
        if isinstance(description, list):
            desc_text = " ".join(str(d) for d in description if d)
        else:
            desc_text = str(description)

        # Supplement with features if description is short
        features = record.get("features", [])
        if isinstance(features, list) and features:
            features_text = "; ".join(str(f) for f in features if f)
            if desc_text:
                desc_text = f"{desc_text}\n\nFeatures: {features_text}"
            else:
                desc_text = features_text

        return desc_text.strip() or "No description available"

    @staticmethod
    def _extract_category(record: dict[str, Any]) -> str:
        """Extract the most specific category from the record."""
        # Try categories list first (most specific last)
        categories = record.get("categories", [])
        if isinstance(categories, list) and categories:
            # Flatten nested lists
            flat = []
            for item in categories:
                if isinstance(item, list):
                    flat.extend(item)
                elif isinstance(item, str):
                    flat.append(item)
            if flat:
                return flat[-1].strip()

        # Fall back to main_category
        main_cat = record.get("main_category", "")
        if main_cat:
            return str(main_cat).strip()

        return "Uncategorized"

    @staticmethod
    def _extract_price(record: dict[str, Any]) -> float:
        """Extract price as a float. Returns 0.0 if unavailable."""
        price = record.get("price")

        if price is None:
            return 0.0

        if isinstance(price, (int, float)):
            return float(price)

        # Handle string prices like "$12.99" or "12.99"
        if isinstance(price, str):
            cleaned = price.replace("$", "").replace(",", "").strip()
            try:
                return float(cleaned)
            except ValueError:
                return 0.0

        return 0.0
