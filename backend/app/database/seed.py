"""Database seeding script for NeedNow AI.

Seeds initial application data (sample products by category) into the
database. Only inserts data if the products table is empty.

Usage:
    python -m app.database.seed
"""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import func, select

from app.database.connection import AsyncSessionLocal
from app.models.product import Product

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Seed Data
# ---------------------------------------------------------------------------

SEED_PRODUCTS: list[dict[str, str | float | int]] = [
    # Groceries
    {"title": "Organic Whole Milk 1L", "description": "Farm-fresh organic whole milk.", "category": "Groceries", "brand": "Nature's Best", "price": 3.49, "stock": 100},
    {"title": "Whole Wheat Bread", "description": "Freshly baked whole wheat bread.", "category": "Groceries", "brand": "Baker's Delight", "price": 2.99, "stock": 80},
    {"title": "Free-Range Eggs (12pk)", "description": "Free-range large eggs.", "category": "Groceries", "brand": "Happy Hens", "price": 4.99, "stock": 120},
    # Medicine
    {"title": "Ibuprofen 200mg (50 tablets)", "description": "Pain relief tablets.", "category": "Medicine", "brand": "HealthPlus", "price": 8.99, "stock": 200},
    {"title": "Digital Thermometer", "description": "Fast-read digital thermometer.", "category": "Medicine", "brand": "MedTech", "price": 12.99, "stock": 60},
    {"title": "First Aid Kit", "description": "Complete home first aid kit.", "category": "Medicine", "brand": "SafeCare", "price": 24.99, "stock": 45},
    # Electronics
    {"title": "USB-C Fast Charger", "description": "65W USB-C wall charger.", "category": "Electronics", "brand": "ChargePro", "price": 29.99, "stock": 150},
    {"title": "Wireless Bluetooth Earbuds", "description": "Noise-cancelling earbuds.", "category": "Electronics", "brand": "SoundWave", "price": 49.99, "stock": 75},
    {"title": "LED Desk Lamp", "description": "Adjustable brightness LED lamp.", "category": "Electronics", "brand": "BrightLife", "price": 34.99, "stock": 90},
    # Home Essentials
    {"title": "Eco-Friendly Dish Soap", "description": "Plant-based dish soap.", "category": "Home Essentials", "brand": "GreenClean", "price": 5.49, "stock": 200},
    {"title": "Microfiber Cleaning Cloths (6pk)", "description": "Reusable cleaning cloths.", "category": "Home Essentials", "brand": "CleanPro", "price": 9.99, "stock": 110},
    {"title": "Bamboo Paper Towels (3 rolls)", "description": "Sustainable bamboo paper towels.", "category": "Home Essentials", "brand": "EcoPure", "price": 7.99, "stock": 130},
]


# ---------------------------------------------------------------------------
# Seed Function
# ---------------------------------------------------------------------------


async def seed_database() -> None:
    """Seed the database with initial product data.

    Checks if the products table is empty before inserting.
    Rolls back on any exception to maintain data integrity.
    """
    async with AsyncSessionLocal() as session:
        try:
            # Check if data already exists
            stmt = select(func.count()).select_from(Product)
            result = await session.execute(stmt)
            count = result.scalar_one()

            if count > 0:
                logger.info(
                    "Database already seeded (%d products exist). Skipping.", count
                )
                return

            # Insert seed products
            products = [Product(**data) for data in SEED_PRODUCTS]
            session.add_all(products)
            await session.commit()

            logger.info(
                "Database seeded successfully: %d products inserted.", len(products)
            )

        except Exception as exc:
            await session.rollback()
            logger.error("Database seeding failed: %s", exc)
            raise


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(seed_database())
