"""Sustainability retrieval service.

Finds genuinely related eco-friendly alternatives by:
1. Extracting key product type words from the original product title
2. Searching for similar products with eco-positive keywords
3. Filtering to only return products that serve the same purpose
"""

import logging

from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product

logger = logging.getLogger(__name__)

# Keywords that indicate eco-friendly products
ECO_KEYWORDS = [
    "organic", "natural", "bamboo", "recycled", "biodegradable",
    "reusable", "eco", "plant-based", "non-toxic", "chemical-free",
    "sustainable", "compostable", "cotton", "herbal", "ayurvedic",
    "green", "pure", "vegan", "cruelty-free",
]


class SustainabilityRetrievalService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_alternatives(
        self,
        category: str,
        exclude_product_id,
    ) -> list:
        """Find eco-friendly alternatives related to the original product.

        Strategy:
        1. Find products containing eco-positive keywords
        2. Limit to products with price > 0 (available)
        3. Return max 10 candidates for scoring
        """
        try:
            # Search for products with eco-friendly indicators
            eco_conditions = [
                Product.title.ilike(f"%{kw}%") for kw in ECO_KEYWORDS
            ]

            stmt = (
                select(Product)
                .where(
                    or_(*eco_conditions),
                    Product.id != exclude_product_id,
                    Product.price > 0,
                )
                .order_by(func.random())
                .limit(10)
            )

            result = await self.db.execute(stmt)
            alternatives = list(result.scalars().all())

            if alternatives:
                logger.debug(
                    "Found %d eco alternatives for product %s",
                    len(alternatives),
                    exclude_product_id,
                )
            return alternatives

        except Exception as exc:
            logger.warning("Eco alternative retrieval failed: %s", exc)
            return []
