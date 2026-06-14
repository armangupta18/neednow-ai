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

    # In-memory cart storage for demo mode (when DB user doesn't exist)
    _demo_carts: dict[str, dict] = {}

    def __init__(self, repository: CartRepository) -> None:
        self._repository = repository
        self._logger = logger

    @classmethod
    def set_demo_cart(cls, user_id: str, products: list[dict]) -> None:
        """Store recommended products as a demo cart (called by chat pipeline)."""
        cls._demo_carts[str(user_id)] = {
            "products": products,
            "total": sum(p.get("price", 0) for p in products),
        }
        logger.info("Demo cart set for user %s: %d products", user_id, len(products))

    @classmethod
    def _has_demo_cart(cls, user_id: str) -> bool:
        return str(user_id) in cls._demo_carts

    @classmethod
    def _get_demo_cart_response(cls, user_id: UUID) -> CartResponse:
        """Build a CartResponse from the demo cart."""
        from uuid import uuid4
        demo = cls._demo_carts.get(str(user_id), {"products": [], "total": 0})
        items = [
            CartItemResponse(
                id=uuid4(),
                product_id=p.get("id", str(uuid4())),
                product_name=p.get("title", "Product"),
                quantity=1,
                unit_price=p.get("price", 0.0),
                line_total=p.get("price", 0.0),
            )
            for p in demo["products"][:10]
        ]
        return CartResponse(
            user_id=user_id,
            cart_id=uuid4(),
            total_amount=demo["total"],
            items=items,
        )

    async def add_item(
        self,
        *,
        user_id: UUID,
        product_id: UUID,
        quantity: int,
    ) -> CartMutationResponse:
        """Add a product to the user's cart."""
        self._logger.info("Adding item to cart: user=%s product=%s qty=%d", user_id, product_id, quantity)

        # Demo cart mode: add product by looking it up from DB
        if self._has_demo_cart(str(user_id)):
            product = await self._repository.get_product(product_id)
            if product is None:
                raise ProductNotFoundError(f"Product {product_id} not found")

            demo = self._demo_carts[str(user_id)]
            # Check if already in cart
            existing = next((p for p in demo["products"] if p.get("id") == str(product_id)), None)
            if not existing:
                demo["products"].append({
                    "id": str(product_id),
                    "title": product.title,
                    "price": product.price,
                    "score": 0.0,
                })
            demo["total"] = sum(p.get("price", 0) for p in demo["products"])
            return CartMutationResponse(
                message="Item added to cart",
                cart=self._get_demo_cart_response(user_id),
            )

        # DB mode
        product = await self._repository.get_product(product_id)
        if product is None:
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
        """Remove or reduce quantity of a product in the user's cart."""
        self._logger.info("Removing item from cart: user=%s product=%s", user_id, product_id)

        # Demo cart mode
        if self._has_demo_cart(str(user_id)):
            demo = self._demo_carts[str(user_id)]
            demo["products"] = [p for p in demo["products"] if p.get("id") != str(product_id)]
            demo["total"] = sum(p.get("price", 0) for p in demo["products"])
            self._logger.info("Item removed from demo cart: %s", product_id)
            return CartMutationResponse(
                message="Item removed from cart",
                cart=self._get_demo_cart_response(user_id),
            )

        # DB mode

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

        Falls back to demo cart (from chat recommendations) if no DB cart exists.
        """
        self._logger.info(
            "Retrieving cart",
            extra={"user_id": str(user_id)},
        )

        cart = await self._repository.get_cart_by_user_id(user_id)
        if cart is not None:
            self._logger.debug(
                "Cart retrieved from DB",
                extra={
                    "cart_id": str(cart.id),
                    "item_count": len(cart.items),
                    "total": cart.total_amount,
                },
            )
            return self._to_cart_response(user_id, cart)

        # Fall back to demo cart (populated by chat pipeline)
        if self._has_demo_cart(str(user_id)):
            self._logger.info("Returning demo cart for user %s", user_id)
            return self._get_demo_cart_response(user_id)

        self._logger.warning(
            "No cart found for user",
            extra={"user_id": str(user_id)},
        )
        raise CartNotFoundError(f"Cart not found for user {user_id}")

    async def clear_cart(self, user_id: UUID) -> CartClearResponse:
        """Clear all items from the user's cart."""
        self._logger.info("Clearing cart: user=%s", user_id)

        # Demo cart mode
        if self._has_demo_cart(str(user_id)):
            self._demo_carts[str(user_id)] = {"products": [], "total": 0}
            self._logger.info("Demo cart cleared for user %s", user_id)
            return CartClearResponse(user_id=user_id)

        # DB mode

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
