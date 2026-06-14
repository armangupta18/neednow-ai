from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.repositories.cart_repository import CartRepository
from app.services.cart_service import CartService


def get_cart_service(
    db: AsyncSession = Depends(get_db),
) -> CartService:
    return CartService(CartRepository(db))
