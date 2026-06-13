from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.product import Product
from app.models.session import Session
from app.models.situation import Situation
from app.models.user import User


class CartRepository:
    """PostgreSQL data access for user carts."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_user(self, user_id: UUID) -> User | None:
        stmt = select(User).where(User.id == user_id)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_product(self, product_id: UUID) -> Product | None:
        stmt = select(Product).where(Product.id == product_id)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_cart_by_user_id(self, user_id: UUID) -> Cart | None:
        stmt = (
            select(Cart)
            .join(Situation, Cart.situation_id == Situation.id)
            .where(Situation.user_id == user_id)
            .options(selectinload(Cart.items).selectinload(CartItem.product))
            .order_by(Cart.updated_at.desc())
            .limit(1)
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create_cart(self, user_id: UUID) -> Cart:
        cart = await self.get_cart_by_user_id(user_id)
        if cart is not None:
            return cart

        user = await self.get_user(user_id)
        if user is None:
            raise ValueError("User not found")

        session = Session(
            user_id=user_id,
            session_token=secrets.token_urlsafe(32),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        self._db.add(session)
        await self._db.flush()

        situation = Situation(
            user_id=user_id,
            session_id=session.id,
            raw_input="Cart created via API",
        )
        self._db.add(situation)
        await self._db.flush()

        cart = Cart(
            situation_id=situation.id,
            total_amount=0.0,
        )
        self._db.add(cart)
        await self._db.commit()
        await self._db.refresh(cart)

        refreshed = await self.get_cart_by_user_id(user_id)
        if refreshed is None:
            raise ValueError("Failed to create cart")
        return refreshed

    async def get_cart_item(
        self,
        cart_id: UUID,
        product_id: UUID,
    ) -> CartItem | None:
        stmt = select(CartItem).where(
            CartItem.cart_id == cart_id,
            CartItem.product_id == product_id,
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def save(self) -> None:
        await self._db.commit()

    async def refresh(self, entity) -> None:
        await self._db.refresh(entity)

    async def delete_item(self, item: CartItem) -> None:
        await self._db.delete(item)

    async def clear_cart_items(self, cart: Cart) -> None:
        for item in list(cart.items):
            await self._db.delete(item)
        cart.items.clear()
        cart.total_amount = 0.0
        await self.save()
