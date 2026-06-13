from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CartAddRequest(BaseModel):
    """Request payload to add a product to the user's cart."""

    model_config = ConfigDict(extra="forbid")

    user_id: UUID
    product_id: UUID
    quantity: int = Field(default=1, ge=1)


class CartRemoveRequest(BaseModel):
    """Request payload to remove a product from the user's cart."""

    model_config = ConfigDict(extra="forbid")

    user_id: UUID
    product_id: UUID
    quantity: int | None = Field(
        default=None,
        ge=1,
        description="Quantity to remove; omit to remove the product entirely",
    )


class CartItemResponse(BaseModel):
    """Single cart line item."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    product_id: UUID
    product_name: str
    quantity: int = Field(ge=1)
    unit_price: float
    line_total: float


class CartResponse(BaseModel):
    """User cart snapshot."""

    model_config = ConfigDict(extra="forbid")

    user_id: UUID
    cart_id: UUID
    total_amount: float
    items: list[CartItemResponse] = Field(default_factory=list)


class CartMutationResponse(BaseModel):
    """Response after adding or removing cart items."""

    model_config = ConfigDict(extra="forbid")

    message: str
    cart: CartResponse


class CartClearResponse(BaseModel):
    """Response after clearing a user's cart."""

    model_config = ConfigDict(extra="forbid")

    user_id: UUID
    cleared: bool = True
    message: str = "Cart cleared successfully"
