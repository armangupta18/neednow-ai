"""Cart repository — PostgreSQL data access for shopping carts.

Implements the repository pattern over SQLAlchemy AsyncSession,
providing typed CRUD operations for Cart and CartItem models.

Dependencies:
    - app.models.cart.Cart
    - app.models.cart_item.CartItem
    - app.models.product.Product
    - app.models.session.Session
    - app.models.situation.Situation
    - sqlalchemy.ext.asyncio.AsyncSession
"""

from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.product import Product
from app.models.session import Session
from app.models.situation import Situation
from app.models.user import User

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class CartRepositoryError(Exception):
    """Base exception for cart repository operations."""


class CartNotFoundError(CartRepositoryError):
    """Raised when a cart cannot be found for the given user."""


class ProductNotFoundError(CartRepositoryError):
    """Raised when a product cannot be found."""


class ItemNotInCartError(CartRepositoryError):
    """Raised when an item is not present in the cart."""


class InvalidQuantityError(CartRepositoryError):
    """Raised when an invalid quantity is provided."""


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------


class CartRepository:
    """PostgreSQL data access for user shopping carts.

    Wraps an AsyncSession and exposes typed async operations for
    cart item management following the repository pattern.

    Args:
        db: SQLAlchemy AsyncSession instance (injected via FastAPI Depends).
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Core Cart Methods
    # ------------------------------------------------------------------

    async def get_cart(self, user_id: UUID) -> Cart:
        """Get the active cart for a user, creating one if necessary.

        Args:
            user_id: UUID of the user.

        Returns:
            Cart instance with items eagerly loaded.

        Raises:
            CartRepositoryError: On unexpected database errors.
        """
        try:
            cart = await self._get_cart_by_user_id(user_id)
            if cart is not None:
                logger.debug("Found cart id=%s for user id=%s", cart.id, user_id)
                return cart

            # Create a new cart
            cart = await self._create_cart(user_id)
            logger.info("Created new cart id=%s for user id=%s", cart.id, user_id)
            return cart

        except CartRepositoryError:
            raise
        except SQLAlchemyError as exc:
            logger.error("Failed to get cart for user id=%s: %s", user_id, exc)
            raise CartRepositoryError(
                f"Failed to retrieve cart for user {user_id}"
            ) from exc

    async def add_item(
        self,
        user_id: UUID,
        product_id: UUID,
        *,
        quantity: int = 1,
    ) -> CartItem:
        """Add an item to the user's cart or increment quantity if it exists.

        Args:
            user_id: UUID of the cart owner.
            product_id: UUID of the product to add.
            quantity: Number of units to add (must be >= 1).

        Returns:
            The created or updated CartItem.

        Raises:
            InvalidQuantityError: If quantity < 1.
            ProductNotFoundError: If the product doesn't exist.
            CartRepositoryError: On unexpected database errors.
        """
        if quantity < 1:
            raise InvalidQuantityError(f"Quantity must be >= 1, got {quantity}")

        try:
            # Validate product exists
            product = await self._get_product(product_id)
            if product is None:
                raise ProductNotFoundError(f"Product {product_id} not found")

            # Get or create cart
            cart = await self.get_cart(user_id)

            # Check if item already in cart
            existing_item = await self._get_cart_item(cart.id, product_id)

            if existing_item is not None:
                # Increment quantity
                existing_item.quantity += quantity
                await self._recalculate_total(cart)
                await self._db.commit()
                await self._db.refresh(existing_item)
                logger.info(
                    "Incremented item product_id=%s in cart id=%s (new qty=%d)",
                    product_id,
                    cart.id,
                    existing_item.quantity,
                )
                return existing_item

            # Create new cart item
            item = CartItem(
                cart_id=cart.id,
                product_id=product_id,
                quantity=quantity,
                unit_price=product.price,
            )
            self._db.add(item)
            await self._recalculate_total(cart, additional_amount=product.price * quantity)
            await self._db.commit()
            await self._db.refresh(item)

            logger.info(
                "Added item product_id=%s to cart id=%s (qty=%d, price=%.2f)",
                product_id,
                cart.id,
                quantity,
                product.price,
            )
            return item

        except (CartRepositoryError, ProductNotFoundError, InvalidQuantityError):
            raise
        except SQLAlchemyError as exc:
            await self._db.rollback()
            logger.error(
                "Failed to add item product_id=%s for user id=%s: %s",
                product_id,
                user_id,
                exc,
            )
            raise CartRepositoryError(f"Failed to add item to cart: {exc}") from exc

    async def remove_item(
        self,
        user_id: UUID,
        product_id: UUID,
    ) -> None:
        """Remove an item entirely from the user's cart.

        Args:
            user_id: UUID of the cart owner.
            product_id: UUID of the product to remove.

        Raises:
            CartNotFoundError: If the user has no active cart.
            ItemNotInCartError: If the product is not in the cart.
            CartRepositoryError: On unexpected database errors.
        """
        try:
            cart = await self._get_cart_by_user_id(user_id)
            if cart is None:
                raise CartNotFoundError(f"No cart found for user {user_id}")

            item = await self._get_cart_item(cart.id, product_id)
            if item is None:
                raise ItemNotInCartError(
                    f"Product {product_id} is not in cart {cart.id}"
                )

            await self._db.delete(item)
            await self._recalculate_total(
                cart, deduct_amount=item.unit_price * item.quantity
            )
            await self._db.commit()

            logger.info(
                "Removed item product_id=%s from cart id=%s",
                product_id,
                cart.id,
            )

        except (CartRepositoryError, ItemNotInCartError):
            raise
        except SQLAlchemyError as exc:
            await self._db.rollback()
            logger.error(
                "Failed to remove item product_id=%s for user id=%s: %s",
                product_id,
                user_id,
                exc,
            )
            raise CartRepositoryError(
                f"Failed to remove item from cart: {exc}"
            ) from exc

    async def update_quantity(
        self,
        user_id: UUID,
        product_id: UUID,
        quantity: int,
    ) -> CartItem:
        """Update the quantity of an item in the user's cart.

        Args:
            user_id: UUID of the cart owner.
            product_id: UUID of the product to update.
            quantity: New quantity (must be >= 1). Use remove_item() to delete.

        Returns:
            The updated CartItem.

        Raises:
            InvalidQuantityError: If quantity < 1.
            CartNotFoundError: If the user has no active cart.
            ItemNotInCartError: If the product is not in the cart.
            CartRepositoryError: On unexpected database errors.
        """
        if quantity < 1:
            raise InvalidQuantityError(
                f"Quantity must be >= 1, got {quantity}. Use remove_item() to delete."
            )

        try:
            cart = await self._get_cart_by_user_id(user_id)
            if cart is None:
                raise CartNotFoundError(f"No cart found for user {user_id}")

            item = await self._get_cart_item(cart.id, product_id)
            if item is None:
                raise ItemNotInCartError(
                    f"Product {product_id} is not in cart {cart.id}"
                )

            old_quantity = item.quantity
            item.quantity = quantity

            # Recalculate total based on quantity difference
            diff = (quantity - old_quantity) * item.unit_price
            cart.total_amount = max(0.0, cart.total_amount + diff)

            await self._db.commit()
            await self._db.refresh(item)

            logger.info(
                "Updated quantity for product_id=%s in cart id=%s: %d → %d",
                product_id,
                cart.id,
                old_quantity,
                quantity,
            )
            return item

        except (CartRepositoryError, InvalidQuantityError, ItemNotInCartError):
            raise
        except SQLAlchemyError as exc:
            await self._db.rollback()
            logger.error(
                "Failed to update quantity for product_id=%s user_id=%s: %s",
                product_id,
                user_id,
                exc,
            )
            raise CartRepositoryError(
                f"Failed to update cart item quantity: {exc}"
            ) from exc

    async def clear_cart(self, user_id: UUID) -> None:
        """Remove all items from the user's cart and reset the total.

        Args:
            user_id: UUID of the cart owner.

        Raises:
            CartNotFoundError: If the user has no active cart.
            CartRepositoryError: On unexpected database errors.
        """
        try:
            cart = await self._get_cart_by_user_id(user_id)
            if cart is None:
                raise CartNotFoundError(f"No cart found for user {user_id}")

            for item in list(cart.items):
                await self._db.delete(item)

            cart.items.clear()
            cart.total_amount = 0.0
            await self._db.commit()

            logger.info("Cleared all items from cart id=%s for user id=%s", cart.id, user_id)

        except CartRepositoryError:
            raise
        except SQLAlchemyError as exc:
            await self._db.rollback()
            logger.error("Failed to clear cart for user id=%s: %s", user_id, exc)
            raise CartRepositoryError(f"Failed to clear cart: {exc}") from exc

    # ------------------------------------------------------------------
    # Legacy Compatibility Methods
    # ------------------------------------------------------------------

    async def get_user(self, user_id: UUID) -> User | None:
        """Retrieve a user by ID."""
        stmt = select(User).where(User.id == user_id)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_product(self, product_id: UUID) -> Product | None:
        """Retrieve a product by ID (public alias)."""
        return await self._get_product(product_id)

    async def get_cart_by_user_id(self, user_id: UUID) -> Cart | None:
        """Retrieve the active cart for a user (public alias)."""
        return await self._get_cart_by_user_id(user_id)

    async def get_or_create_cart(self, user_id: UUID) -> Cart:
        """Get or create a cart for the user (public alias)."""
        return await self.get_cart(user_id)

    async def get_cart_item(
        self,
        cart_id: UUID,
        product_id: UUID,
    ) -> CartItem | None:
        """Retrieve a specific cart item (public alias)."""
        return await self._get_cart_item(cart_id, product_id)

    async def save(self) -> None:
        """Flush and commit the current session."""
        try:
            await self._db.commit()
        except SQLAlchemyError as exc:
            await self._db.rollback()
            logger.error("Failed to save session: %s", exc)
            raise CartRepositoryError("Failed to save session") from exc

    async def refresh(self, entity: object) -> None:
        """Refresh an entity from the database."""
        await self._db.refresh(entity)

    async def delete_item(self, item: CartItem) -> None:
        """Delete a cart item directly."""
        await self._db.delete(item)

    async def clear_cart_items(self, cart: Cart) -> None:
        """Clear all items from a cart instance (legacy method)."""
        for item in list(cart.items):
            await self._db.delete(item)
        cart.items.clear()
        cart.total_amount = 0.0
        await self.save()

    # ------------------------------------------------------------------
    # Private Helpers
    # ------------------------------------------------------------------

    async def _get_cart_by_user_id(self, user_id: UUID) -> Cart | None:
        """Retrieve the most recent active cart for a user."""
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

    async def _get_cart_item(
        self, cart_id: UUID, product_id: UUID
    ) -> CartItem | None:
        """Retrieve a specific item from a cart."""
        stmt = select(CartItem).where(
            CartItem.cart_id == cart_id,
            CartItem.product_id == product_id,
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_product(self, product_id: UUID) -> Product | None:
        """Retrieve a product by ID."""
        stmt = select(Product).where(Product.id == product_id)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def _create_cart(self, user_id: UUID) -> Cart:
        """Create a new cart with associated session and situation."""
        user = await self.get_user(user_id)
        if user is None:
            raise CartNotFoundError(f"User {user_id} not found — cannot create cart")

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

        # Re-fetch with eager loading
        refreshed = await self._get_cart_by_user_id(user_id)
        if refreshed is None:
            raise CartRepositoryError("Failed to create cart")
        return refreshed

    async def _recalculate_total(
        self,
        cart: Cart,
        *,
        additional_amount: float = 0.0,
        deduct_amount: float = 0.0,
    ) -> None:
        """Recalculate the cart total amount."""
        cart.total_amount = max(
            0.0, cart.total_amount + additional_amount - deduct_amount
        )
