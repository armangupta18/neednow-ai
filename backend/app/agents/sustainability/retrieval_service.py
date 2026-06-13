from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product


class SustainabilityRetrievalService:

    def __init__(
        self,
        db: AsyncSession,
    ):
        self.db = db

    async def find_alternatives(
        self,
        category: str,
        exclude_product_id,
    ):

        stmt = (
            select(Product)
            .where(
                Product.category == category,
                Product.id != exclude_product_id,
            )
            .limit(20)
        )

        result = await self.db.execute(stmt)

        return result.scalars().all()