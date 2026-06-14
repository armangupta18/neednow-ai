"""Dataset verification script for NeedNow AI.

Validates the presence and integrity of all datasets, database tables,
and vector store collections required by the platform.

Usage:
    python scripts/verify_datasets.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ---------------------------------------------------------------------------
# Verification Checks
# ---------------------------------------------------------------------------

PASS = "✅"
FAIL = "❌"
WARN = "⚠️"


def check_file(path: str, description: str) -> tuple[str, str]:
    """Check if a file exists and report its size."""
    p = Path(path)
    if p.exists():
        size = p.stat().st_size
        if size == 0:
            return WARN, f"{description}: EXISTS but EMPTY ({path})"
        size_str = _format_size(size)
        # Count lines/records for JSON/JSONL
        extra = ""
        if path.endswith(".jsonl"):
            with open(p) as f:
                lines = sum(1 for _ in f)
            extra = f" ({lines:,} records)"
        elif path.endswith(".json"):
            try:
                with open(p) as f:
                    data = json.load(f)
                if isinstance(data, list):
                    extra = f" ({len(data):,} records)"
                elif isinstance(data, dict):
                    extra = f" ({len(data):,} entries)"
            except (json.JSONDecodeError, IOError):
                extra = " (invalid JSON)"
        return PASS, f"{description}: {size_str}{extra}"
    else:
        return FAIL, f"{description}: NOT FOUND ({path})"


async def check_postgres() -> tuple[str, str]:
    """Check PostgreSQL product count."""
    try:
        from sqlalchemy import func, select
        from app.database.connection import AsyncSessionLocal
        from app.models.product import Product

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(func.count()).select_from(Product)
            )
            count = result.scalar_one()

        if count > 0:
            return PASS, f"PostgreSQL products table: {count:,} records"
        else:
            return WARN, "PostgreSQL products table: 0 records (empty)"

    except Exception as exc:
        return FAIL, f"PostgreSQL connection failed: {exc}"


def check_chromadb() -> tuple[str, str, str, str]:
    """Check ChromaDB collection and embedding count."""
    chroma_path = "datasets/embeddings/chroma_db"
    collection_status = (FAIL, "ChromaDB collection: NOT FOUND")
    embedding_status = (FAIL, "Embeddings count: UNAVAILABLE")

    if not Path(chroma_path).exists():
        collection_status = (FAIL, f"ChromaDB storage: NOT FOUND ({chroma_path})")
        return *collection_status, *embedding_status

    try:
        import chromadb
        from chromadb.config import Settings as ChromaSettings

        client = chromadb.PersistentClient(
            path=chroma_path,
            settings=ChromaSettings(anonymized_telemetry=False),
        )

        collections = client.list_collections()
        if collections:
            col_names = [c.name for c in collections]
            collection_status = (PASS, f"ChromaDB collections: {col_names}")

            # Get product collection count
            try:
                products_col = client.get_collection("products")
                count = products_col.count()
                if count > 0:
                    embedding_status = (PASS, f"Embeddings count: {count:,} vectors")
                else:
                    embedding_status = (WARN, "Embeddings count: 0 (empty collection)")
            except Exception:
                embedding_status = (WARN, "Embeddings count: 'products' collection not found")
        else:
            collection_status = (WARN, f"ChromaDB storage exists but no collections")
            embedding_status = (WARN, "Embeddings count: no collections")

    except ImportError:
        collection_status = (FAIL, "ChromaDB: package not installed")
        embedding_status = (FAIL, "Embeddings count: chromadb not installed")
    except Exception as exc:
        collection_status = (FAIL, f"ChromaDB error: {exc}")
        embedding_status = (FAIL, f"Embeddings count: {exc}")

    return *collection_status, *embedding_status


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _format_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes >= 1_073_741_824:
        return f"{size_bytes / 1_073_741_824:.1f} GB"
    if size_bytes >= 1_048_576:
        return f"{size_bytes / 1_048_576:.1f} MB"
    if size_bytes >= 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes} B"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def main() -> None:
    """Run all verification checks and print report."""

    print()
    print("=" * 65)
    print("  NeedNow AI — Dataset & Infrastructure Verification Report")
    print("=" * 65)
    print()

    results: list[tuple[str, str]] = []
    total_pass = 0
    total_fail = 0
    total_warn = 0

    # ------------------------------------------------------------------
    # 1. Product Dataset
    # ------------------------------------------------------------------
    print("─── 1. Product Dataset ───")
    r = check_file(
        "datasets/products/meta_Health_and_Personal_Care.jsonl",
        "Health & Personal Care JSONL",
    )
    results.append(r)
    print(f"  {r[0]} {r[1]}")
    print()

    # ------------------------------------------------------------------
    # 2. PostgreSQL Product Count
    # ------------------------------------------------------------------
    print("─── 2. PostgreSQL Database ───")
    r = await check_postgres()
    results.append(r)
    print(f"  {r[0]} {r[1]}")
    print()

    # ------------------------------------------------------------------
    # 3 & 4. ChromaDB Collection & Embedding Count
    # ------------------------------------------------------------------
    print("─── 3. ChromaDB Vector Store ───")
    s1, m1, s2, m2 = check_chromadb()
    results.append((s1, m1))
    results.append((s2, m2))
    print(f"  {s1} {m1}")
    print(f"  {s2} {m2}")
    print()

    # ------------------------------------------------------------------
    # 5. Sustainability Dataset
    # ------------------------------------------------------------------
    print("─── 4. Sustainability Dataset ───")
    r = check_file(
        "datasets/sustainability/sustainability_scores.json",
        "Sustainability scores",
    )
    results.append(r)
    print(f"  {r[0]} {r[1]}")
    print()

    # ------------------------------------------------------------------
    # 6. Mock Datasets
    # ------------------------------------------------------------------
    print("─── 5. Mock Datasets ───")
    mock_files = [
        ("datasets/mock-data/users.json", "Mock users"),
        ("datasets/mock-data/preferences.json", "Mock preferences"),
        ("datasets/mock-data/purchases.json", "Mock purchases"),
        ("datasets/mock-data/conversations.json", "Mock conversations"),
    ]
    for path, desc in mock_files:
        r = check_file(path, desc)
        results.append(r)
        print(f"  {r[0]} {r[1]}")
    print()

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    for status, _ in results:
        if status == PASS:
            total_pass += 1
        elif status == FAIL:
            total_fail += 1
        elif status == WARN:
            total_warn += 1

    total = len(results)

    print("=" * 65)
    print(f"  SUMMARY: {total_pass}/{total} passed, {total_warn} warnings, {total_fail} failures")
    print("=" * 65)

    if total_fail == 0 and total_warn == 0:
        print(f"\n  {PASS} All datasets and infrastructure verified successfully!\n")
    elif total_fail == 0:
        print(f"\n  {WARN} Verification passed with warnings. Review above.\n")
    else:
        print(f"\n  {FAIL} Some checks failed. Run the relevant setup scripts:\n")
        print("    python scripts/load_products.py                    # Load products to PostgreSQL")
        print("    python scripts/generate_product_embeddings.py      # Generate ChromaDB embeddings")
        print("    python scripts/generate_sustainability_scores.py   # Generate sustainability scores")
        print()

    sys.exit(0 if total_fail == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
