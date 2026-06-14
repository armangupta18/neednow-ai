"""Order schemas — Pydantic models for order API endpoints."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class OrderItemInput(BaseModel):
    """Single item in an order."""

    product_id: str
    product_name: str
    quantity: int = Field(ge=1)
    unit_price: float = Field(ge=0)


class OrderAddress(BaseModel):
    """Delivery address for an order."""

    name: str
    phone: str
    address: str
    landmark: str = ""
    city: str
    state: str
    pincode: str


class OrderCreateRequest(BaseModel):
    """Request body to place a new order."""

    user_id: UUID
    cart_items: list[OrderItemInput]
    address: OrderAddress
    payment_method: str  # "cod" | "upi" | "credit_card" | "debit_card" | "net_banking"
    total_amount: float = Field(ge=0)


class OrderResponse(BaseModel):
    """Single order response."""

    order_id: str
    status: str  # "confirmed"
    estimated_delivery: str
    total_amount: float
    payment_method: str
    address: OrderAddress
    items: list[OrderItemInput]
    created_at: str


class OrderListResponse(BaseModel):
    """List of orders for a user."""

    orders: list[OrderResponse]
