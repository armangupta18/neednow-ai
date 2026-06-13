from __future__ import annotations

import logging
from uuid import UUID

from app.models.cart_item import CartItem
from app.repositories.cart_repository import CartRepository
from app.schemas.cart import (
    CartClearResponse,
    CartItemResponse,
    CartMutationResponse,
    CartResponse,
)

logger = logging.getLogger(__name__)


class CartServiceError(Exception):
    """Base exception for cart service errors."""

    pass


class CartNotFoundError(CartServiceError):
    """Raised when cart cannot be created or retrieved."""

    pass


class ProductNotFoundError(CartServiceError):
    """Raised when product is not found."""

    pass


class InsufficientStockError(CartServiceError):
    """Raised when product stock is insufficient."""

    pass


class CartService:
    """Business logic for user cart operations."""

    def __init__(self, repository: CartRepository) -> None:
        self._repository = repository
        self._logger = logger

    async def add_item(
        self,
        *,
        user_id: UUID,
        product_id: UUID,
        quantity: int,
    ) -> CartMutationResponse:
        """Add or update a product in the user's cart.

        Raises:
            ProductNotFoundError: If product does not exist.
            InsufficientStockError: If insufficient stock available.
            CartNotFoundError: If cart cannot be retrieved or created.
        """
        self._logger.info(
            "Adding item to cart",
            extra={
                "user_id": str(user_id),
                "product_id": str(product_id),
                "quantity": quantity,
            },
        )

        product = await self._repository.get_product(product_id)
        if product is None:
            self._logger.warning(
                "Product not found",
                extra={"product_id": str(product_id)},
            )
            raise ProductNotFoundError(f"Product {product_id} not found")

        if product.stock < quantity:
            self._logger.warning(
                "Insufficient stock",
                extra={
                    "product_id": str(product_id),
                    "requested": quantity,
                    "available": product.stock,
                },
            )
            raise InsufficientStockError(
                f"Insufficient stock for product {product_id}"
            )

        try:
            cart = await self._repository.get_or_create_cart(user_id)
        except ValueError as exc:
            self._logger.error(
                "Failed to create or retrieve cart",
                extra={"user_id": str(user_id)},
            )
            raise CartNotFoundError(str(exc)) from exc

        existing_item = await self._repository.get_cart_item(cart.id, product_id)

        if existing_item is not None:
            existing_item.quantity += quantity
            self._logger.debug(
                "Updated existing cart item quantity",
                extra={
                    "cart_item_id": str(existing_item.id),
                    "new_quantity": existing_item.quantity,
                },
            )
        else:
            new_item = CartItem(
                cart_id=cart.id,
                product_id=product_id,
                quantity=quantity,
                unit_price=product.price,
            )
            cart.items.append(new_item)
            self._logger.debug(
                "Added new cart item",
                extra={
                    "product_id": str(product_id),
                    "quantity": quantity,
                    "unit_price": product.price,
                },
            )

        cart.total_amount = self._calculate_total(cart)
        await self._repository.save()
        cart = await self._repository.get_cart_by_user_id(user_id)
        if cart is None:
            self._logger.error(
                "Cart not found after update",
                extra={"user_id": str(user_id)},
            )
            raise CartNotFoundError(f"Cart not found after update for user {user_id}")

        self._logger.info(
            "Item added to cart successfully",
            extra={
                "user_id": str(user_id),
                "cart_id": str(cart.id),
                "cart_total": cart.total_amount,
            },
        )

        cart_response = self._to_cart_response(user_id, cart)
        return CartMutationResponse(
            message="Item added to cart",
            cart=cart_response,
        )

    async def remove_item(
        self,
        *,
        user_id: UUID,
        product_id: UUID,
        quantity: int | None = None,
    ) -> CartMutationResponse:
        """Remove or reduce quantity of a product in the user's cart.

        If quantity is None, removes the entire product from cart.
        Otherwise, reduces quantity by the specified amount.

        Raises:
            CartNotFoundError: If cart is not found.
            ProductNotFoundError: If product is not in cart.
        """
        self._logger.info(
            "Removing item from cart",
            extra={
                "user_id": str(user_id),
                "product_id": str(product_id),
                "quantity": quantity,
            },
        )

        cart = await self._repository.get_cart_by_user_id(user_id)
        if cart is None:
            self._logger.warning(
                "Cart not found for user",
                extra={"user_id": str(user_id)},
            )
            raise CartNotFoundError(f"Cart not found for user {user_id}")

        item = await self._repository.get_cart_item(cart.id, product_id)
        if item is None:
            self._logger.warning(
                "Product not in cart",
                extra={
                    "cart_id": str(cart.id),
                    "product_id": str(product_id),
                },
            )
            raise ProductNotFoundError(
                f"Product {product_id} not in cart {cart.id}"
            )

        if quantity is not None and quantity < item.quantity:
            item.quantity -= quantity
            self._logger.debug(
                "Reduced cart item quantity",
                extra={
                    "cart_item_id": str(item.id),
                    "new_quantity": item.quantity,
                },
            )
        else:
            await self._repository.delete_item(item)
            if item in cart.items:
                cart.items.remove(item)
            self._logger.debug(
                "Removed cart item",
                extra={"cart_item_id": str(item.id)},
            )

        cart.total_amount = self._calculate_total(cart)
        await self._repository.save()
        cart = await self._repository.get_cart_by_user_id(user_id)
        if cart is None:
            self._logger.error(
                "Cart not found after update",
                extra={"user_id": str(user_id)},
            )
            raise CartNotFoundError(f"Cart not found after update for user {user_id}")

        self._logger.info(
            "Item removed from cart successfully",
            extra={
                "user_id": str(user_id),
                "cart_id": str(cart.id),
                "cart_total": cart.total_amount,
            },
        )

        cart_response = self._to_cart_response(user_id, cart)
        return CartMutationResponse(
            message="Item removed from cart",
            cart=cart_response,
        )

    async def get_cart(self, user_id: UUID) -> CartResponse:
        """Retrieve the user's current cart.

        Raises:
            CartNotFoundError: If cart is not found.
        """
        self._logger.info(
            "Retrieving cart",
            extra={"user_id": str(user_id)},
        )

        cart = await self._repository.get_cart_by_user_id(user_id)
        if cart is None:
            self._logger.warning(
                "Cart not found for user",
                extra={"user_id": str(user_id)},
            )
            raise CartNotFoundError(f"Cart not found for user {user_id}")

        self._logger.debug(
            "Cart retrieved",
            extra={
                "cart_id": str(cart.id),
                "item_count": len(cart.items),
                "total": cart.total_amount,
            },
        )

        return self._to_cart_response(user_id, cart)

    async def clear_cart(self, user_id: UUID) -> CartClearResponse:
        """Clear all items from the user's cart.

        Raises:
            CartNotFoundError: If cart is not found.
        """
        self._logger.info(
            "Clearing cart",
            extra={"user_id": str(user_id)},
        )

        cart = await self._repository.get_cart_by_user_id(user_id)
        if cart is None:
            self._logger.warning(
                "Cart not found for user",
                extra={"user_id": str(user_id)},
            )
            raise CartNotFoundError(f"Cart not found for user {user_id}")

        await self._repository.clear_cart_items(cart)

        self._logger.info(
            "Cart cleared successfully",
            extra={"user_id": str(user_id), "cart_id": str(cart.id)},
        )

        return CartClearResponse(user_id=user_id)

    async def calculate_total(self, user_id: UUID) -> float:
        """Get the total amount for the user's cart.

        Raises:
            CartNotFoundError: If cart is not found.
        """
        cart = await self._repository.get_cart_by_user_id(user_id)
        if cart is None:
            self._logger.warning(
                "Cart not found for user",
                extra={"user_id": str(user_id)},
            )
            raise CartNotFoundError(f"Cart not found for user {user_id}")

        total = self._calculate_total(cart)
        self._logger.debug(
            "Cart total calculated",
            extra={"user_id": str(user_id), "total": total},
        )

        return total

    @staticmethod
    def _calculate_total(cart) -> float:
        return round(
            sum(item.unit_price * item.quantity for item in cart.items),
            2,
        )

    @staticmethod
    def _to_cart_response(user_id: UUID, cart) -> CartResponse:
        items = [
            CartItemResponse(
                id=item.id,
                product_id=item.product_id,
                product_name=item.product.title if item.product else "Unknown product",
                quantity=item.quantity,
                unit_price=item.unit_price,
                line_total=round(item.unit_price * item.quantity, 2),
            )
            for item in cart.items
        ]

        return CartResponse(
            user_id=user_id,
            cart_id=cart.id,
            total_amount=cart.total_amount,
            items=items,
        )
