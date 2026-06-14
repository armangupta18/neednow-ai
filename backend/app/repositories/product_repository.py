"""Product repository — PostgreSQL data access for product catalog."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product


class ProductRepository:
    """PostgreSQL data access for products."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id(self, product_id: UUID) -> Product | None:
        stmt = select(Product).where(Product.id == product_id)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_title(self, title: str) -> Product | None:
        stmt = select(Product).where(Product.title == title)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self, *, limit: int = 100, offset: int = 0) -> list[Product]:
        stmt = select(Product).limit(limit).offset(offset)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def search_by_category(
        self, category: str, *, limit: int = 50
    ) -> list[Product]:
        stmt = (
            select(Product)
            .where(Product.category == category)
            .limit(limit)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def search_by_brand(
        self, brand: str, *, limit: int = 50
    ) -> list[Product]:
        stmt = (
            select(Product)
            .where(Product.brand == brand)
            .limit(limit)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def count(self) -> int:
        stmt = select(func.count()).select_from(Product)
        result = await self._db.execute(stmt)
        return result.scalar_one()

    async def create(self, product: Product) -> Product:
        self._db.add(product)
        await self._db.commit()
        await self._db.refresh(product)
        return product

    async def create_batch(self, products: list[Product]) -> list[Product]:
        self._db.add_all(products)
        await self._db.commit()
        for p in products:
            await self._db.refresh(p)
        return products

    async def update(self, product: Product) -> Product:
        await self._db.commit()
        await self._db.refresh(product)
        return product

    async def delete(self, product: Product) -> None:
        await self._db.delete(product)
        await self._db.commit()

    async def save(self) -> None:
        await self._db.commit()
