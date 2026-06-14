"""Order Service — persistent order management.

Stores orders in a JSON file for durability across restarts.
Also clears the cart after successful order placement.
"""

from __future__ import annotations

import json
import logging
import os
import random
import string
from datetime import datetime, timedelta
from pathlib import Path
from uuid import UUID

from app.schemas.order import (
    OrderAddress,
    OrderCreateRequest,
    OrderItemInput,
    OrderListResponse,
    OrderResponse,
)

logger = logging.getLogger(__name__)

# Persistent storage file path
ORDERS_FILE = Path("data/orders.json")


class OrderServiceError(Exception):
    """Base exception for order service errors."""
    pass


class OrderNotFoundError(OrderServiceError):
    """Raised when an order cannot be found."""
    pass


class OrderService:
    """Business logic for order placement and retrieval.

    Uses JSON file persistence — orders survive restart and navigation.
    """

    def __init__(self) -> None:
        self._ensure_storage()

    @staticmethod
    def _ensure_storage() -> None:
        """Create data directory and orders file if they don't exist."""
        ORDERS_FILE.parent.mkdir(parents=True, exist_ok=True)
        if not ORDERS_FILE.exists():
            ORDERS_FILE.write_text("[]")

    def _load_orders(self) -> list[dict]:
        """Load all orders from disk."""
        try:
            content = ORDERS_FILE.read_text()
            return json.loads(content) if content.strip() else []
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _save_orders(self, orders: list[dict]) -> None:
        """Persist all orders to disk."""
        self._ensure_storage()
        ORDERS_FILE.write_text(json.dumps(orders, indent=2, default=str))

    @staticmethod
    def _generate_order_id() -> str:
        """Generate order ID in format: NN-XXXXXXXX."""
        chars = string.ascii_uppercase + string.digits
        suffix = "".join(random.choices(chars, k=8))
        return f"NN-{suffix}"

    @staticmethod
    def _estimate_delivery() -> str:
        """Generate estimated delivery time (30-60 min from now)."""
        minutes = random.randint(30, 60)
        delivery_time = datetime.now() + timedelta(minutes=minutes)
        return delivery_time.strftime("%I:%M %p, %d %b %Y")

    async def place_order(self, request: OrderCreateRequest) -> OrderResponse:
        """Place a new order and persist it.

        Also clears the user's demo cart after successful placement.
        """
        order_id = self._generate_order_id()
        now = datetime.now()

        order_data = {
            "order_id": order_id,
            "user_id": str(request.user_id),
            "status": "confirmed",
            "estimated_delivery": self._estimate_delivery(),
            "total_amount": request.total_amount,
            "payment_method": request.payment_method,
            "address": request.address.model_dump(),
            "items": [item.model_dump() for item in request.cart_items],
            "created_at": now.isoformat(),
        }

        # Persist order
        orders = self._load_orders()
        orders.append(order_data)
        self._save_orders(orders)

        # Clear the user's demo cart
        self._clear_user_cart(str(request.user_id))

        logger.info(
            "Order placed & persisted | order_id=%s | user=%s | items=%d | total=%.2f",
            order_id,
            str(request.user_id),
            len(request.cart_items),
            request.total_amount,
        )

        return self._to_response(order_data)

    async def get_orders(self, user_id: UUID) -> OrderListResponse:
        """Get all orders for a user (most recent first)."""
        user_key = str(user_id)
        all_orders = self._load_orders()
        user_orders = [o for o in all_orders if o.get("user_id") == user_key]
        user_orders.reverse()  # Most recent first

        return OrderListResponse(
            orders=[self._to_response(o) for o in user_orders]
        )

    async def get_order(self, user_id: UUID, order_id: str) -> OrderResponse | None:
        """Get a single order by ID."""
        user_key = str(user_id)
        all_orders = self._load_orders()

        for o in all_orders:
            if o.get("order_id") == order_id and o.get("user_id") == user_key:
                return self._to_response(o)

        return None

    @staticmethod
    def _to_response(order_data: dict) -> OrderResponse:
        """Convert raw order dict to OrderResponse."""
        return OrderResponse(
            order_id=order_data["order_id"],
            status=order_data["status"],
            estimated_delivery=order_data["estimated_delivery"],
            total_amount=order_data["total_amount"],
            payment_method=order_data["payment_method"],
            address=OrderAddress(**order_data["address"]),
            items=[OrderItemInput(**item) for item in order_data["items"]],
            created_at=order_data["created_at"],
        )

    @staticmethod
    def _clear_user_cart(user_id: str) -> None:
        """Clear the demo cart for a user after order placement."""
        try:
            from app.services.cart_service import CartService
            if CartService._has_demo_cart(user_id):
                CartService._demo_carts[user_id] = {"products": [], "total": 0}
                logger.info("Cart cleared after order for user %s", user_id)
        except Exception as exc:
            logger.warning("Failed to clear cart after order: %s", exc)
