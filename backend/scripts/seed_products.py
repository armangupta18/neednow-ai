"""Seed the database with a curated list of products.

This script creates Product records for the provided category lists.
It generates a short description, a brand, price, stock and placeholder
image URL for each product. Existing titles are skipped to avoid
duplicates.

Usage:
    python scripts/seed_products.py --dry-run
    python scripts/seed_products.py

Be sure `backend/.env` contains a reachable `DATABASE_URL`.
"""
from __future__ import annotations

import asyncio
import random
import argparse
from pathlib import Path
import sys

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database.connection import AsyncSessionLocal, init_db
from app.models.product import Product


PRODUCT_GROUPS = {
    "Clothing & Fashion": [
        "Cotton T-Shirt",
        "Linen Shirt",
        "Denim Jeans",
        "Casual Joggers",
        "Kurta",
        "Saree",
        "Hoodie",
        "Formal Shirt",
        "Sports Shorts",
        "Casual Dress",
    ],
    "Electronics": [
        "Smartphone",
        "Wireless Earbuds",
        "Bluetooth Speaker",
        "Smartwatch",
        "Laptop",
        "Tablet",
        "Power Bank",
        "Wireless Keyboard",
        "USB-C Charger",
        "LED Monitor",
    ],
    "Home & Kitchen": [
        "Stainless Steel Water Bottle",
        "Electric Kettle",
        "Air Fryer",
        "Mixer Grinder",
        "Pressure Cooker",
        "Food Storage Containers",
        "Non-Stick Pan",
        "Kitchen Chopper",
        "Lunch Box",
        "Coffee Maker",
    ],
    "Beauty & Personal Care": [
        "Face Wash",
        "Moisturizer",
        "Sunscreen",
        "Shampoo",
        "Conditioner",
        "Body Wash",
        "Lip Balm",
        "Face Serum",
        "Hair Oil",
        "Deodorant",
    ],
    "Groceries & Food": [
        "Oats",
        "Rice",
        "Wheat Flour",
        "Lentils",
        "Cooking Oil",
        "Nuts",
        "Peanut Butter",
        "Breakfast Cereal",
        "Green Tea",
        "Snack Bars",
    ],
    "Health & Wellness": [
        "Protein Powder",
        "Electrolyte Powder",
        "Multivitamins",
        "Protein Bars",
        "Herbal Tea",
        "Yoga Mat",
        "Foam Roller",
        "Resistance Bands",
        "Massage Gun",
        "Fitness Tracker",
    ],
    "Sports & Fitness": [
        "Running Shoes",
        "Training Shoes",
        "Gym T-Shirt",
        "Track Pants",
        "Sports Shorts",
        "Dumbbells",
        "Resistance Bands",
        "Skipping Rope",
        "Gym Gloves",
        "Sports Bottle",
    ],
    "Home & Living": [
        "Bedsheet",
        "Pillow",
        "Blanket",
        "Curtains",
        "Floor Mat",
        "Table Lamp",
        "Storage Basket",
        "Cushion Covers",
        "Wall Clock",
        "Indoor Plant Pot",
    ],
    "Beauty, Grooming & Accessories": [
        "Trimmer",
        "Hair Dryer",
        "Hair Straightener",
        "Electric Shaver",
        "Makeup Brush Set",
        "Perfume",
        "Comb",
        "Hair Styling Brush",
        "Face Roller",
        "Manicure Set",
    ],
    "Baby & Kids": [
        "Baby Clothes",
        "Diapers",
        "Baby Wipes",
        "Feeding Bottle",
        "Baby Shampoo",
        "Baby Lotion",
        "Building Blocks",
        "Educational Puzzle",
        "School Backpack",
        "Drawing Kit",
    ],
    "Gifts - Women": [
        "Jewelry Set",
        "Silk Scarf",
        "Spa Gift Basket",
        "Perfume Gift Set",
        "Handbag",
        "Personalized Mug",
        "Scented Candle Set",
        "Makeup Palette",
        "Yoga Gift Pack",
        "Photo Frame",
    ],
    "Gifts - Men": [
        "Leather Wallet",
        "Watch",
        "Grooming Kit",
        "Travel Duffel Bag",
        "Wireless Earbuds Gift",
        "Tool Kit",
        "Whiskey Glasses Set",
        "Tie & Cufflinks",
        "Shaving Set",
        "Personalized Keychain",
    ],
    "Gifts - Kids": [
        "Plush Toy",
        "Children's Book Set",
        "Toy Car",
        "Educational Puzzle",
        "Coloring Kit",
        "Building Blocks Gift",
        "Kids Headphones",
        "School Backpack Gift",
        "Activity Playset",
        "Kids Water Bottle",
    ],
    "Party Snacks": [
        "Potato Chips Party Pack",
        "Nacho Chips",
        "Mixed Nuts Party Bowl",
        "Pretzel Sticks",
        "Popcorn (Buttery)",
        "Cheese Crackers",
        "Olives Jar",
        "Salsa Dip",
        "Mini Sausages",
        "Party Chocolate Box",
    ],
    "Healthy Snacks": [
        "Roasted Almonds",
        "Granola Bars",
        "Dried Fruit Mix",
        "Protein Cookies",
        "Kale Chips",
        "Greek Yogurt Cups",
        "Veggie Sticks",
        "Hummus Snack Pack",
        "Seaweed Snacks",
        "Oatmeal Bites",
    ],
    "Healthy Diets": [
        "Keto Meal Plan Pack",
        "Gluten Free Mix",
        "Low Carb Pasta",
        "Vegan Protein Mix",
        "Detox Green Powder",
        "High Fiber Cereal",
        "Meal Replacement Shake",
        "Organic Quinoa",
        "Chia Seeds",
        "Olive Oil (Extra Virgin)",
    ],
}


SAMPLE_BRANDS = [
    "Acme", "Nexa", "HomeEase", "PureLife", "FitForm", "BrightCo", "Sunrise", "BluePeak"
]


def make_description(title: str, category: str) -> str:
    return (
        f"{title} — high quality {category.lower()} product. Comfortable, durable, and "
        "designed for everyday use. Ideal choice for customers looking for value and reliability."
    )


def price_for_category(category: str) -> float:
    base_ranges = {
        "Electronics": (15.0, 999.0),
        "Clothing & Fashion": (5.0, 120.0),
        "Home & Kitchen": (8.0, 350.0),
        "Beauty & Personal Care": (2.0, 60.0),
        "Groceries & Food": (1.0, 25.0),
        "Health & Wellness": (5.0, 300.0),
        "Sports & Fitness": (5.0, 200.0),
        "Home & Living": (5.0, 250.0),
        "Beauty, Grooming & Accessories": (5.0, 150.0),
        "Baby & Kids": (2.0, 120.0),
    }
    lo, hi = base_ranges.get(category, (5.0, 100.0))
    return round(random.uniform(lo, hi), 2)


async def seed(dry_run: bool = False) -> None:
    # Ensure tables exist
    await init_db()

    created = 0
    skipped = 0

    async with AsyncSessionLocal() as session:
        for category, titles in PRODUCT_GROUPS.items():
            for title in titles:
                # Skip existing by exact title
                existing = await session.execute(
                    Product.__table__.select().where(Product.title == title)
                )
                row = existing.first()
                if row:
                    skipped += 1
                    continue

                p = Product(
                    title=title,
                    description=make_description(title, category),
                    category=category,
                    brand=random.choice(SAMPLE_BRANDS),
                    price=price_for_category(category),
                    stock=random.randint(0, 200),
                    image_url=f"https://example.com/images/{title.replace(' ', '_').lower()}.jpg",
                )

                if not dry_run:
                    session.add(p)
                created += 1

        if not dry_run:
            await session.commit()

    print(f"Seeding complete — created={created} skipped={skipped} (dry_run={dry_run})")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed DB with curated product list")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be created without inserting")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(seed(dry_run=args.dry_run))
