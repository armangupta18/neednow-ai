"""List products from the application's database.

Usage:
    python scripts/list_products.py --limit 50

This script uses the project's async DB session and prints a simple
table of `id`, `title`, `price`, `stock`, and `category` for the first
`--limit` products.
"""
from __future__ import annotations

import asyncio
import argparse
from typing import Optional

from sqlalchemy import select

# Ensure project root is on path when run from repository root
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database.connection import AsyncSessionLocal
from app.models.product import Product


async def list_products(limit: int) -> None:
    async with AsyncSessionLocal() as session:
        stmt = select(Product).limit(limit)
        result = await session.execute(stmt)
        rows = result.scalars().all()

        if not rows:
            print("No products found in database.")
            return

        print(f"Found {len(rows)} products (showing up to {limit}):\n")
        for p in rows:
            print(f"- {p.id} | {p.title[:60]}{'...' if len(p.title)>60 else ''} | ${p.price:.2f} | stock={p.stock} | {p.category}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="List products from DB")
    parser.add_argument("--limit", type=int, default=50, help="How many products to show")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(list_products(args.limit))
