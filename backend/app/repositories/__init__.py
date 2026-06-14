"""Repositories package for NeedNow AI.

Provides SQLAlchemy-based data access layer for all domain entities.
Each repository wraps an AsyncSession and exposes typed CRUD operations.

Usage:
    from app.repositories import (
        UserRepository,
        CartRepository,
        MemoryRepository,
        ProductRepository,
        RecommendationRepository,
    )
"""

from app.repositories.cart_repository import CartRepository
from app.repositories.memory_repository import MemoryRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.recommendation_repository import RecommendationRepository
from app.repositories.user_repository import UserRepository

__all__: list[str] = [
    "UserRepository",
    "CartRepository",
    "MemoryRepository",
    "ProductRepository",
    "RecommendationRepository",
]
