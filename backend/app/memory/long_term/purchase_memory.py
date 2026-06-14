"""Long-term purchase memory module.

Stores and retrieves historical purchase data for a user,
enabling repeat-purchase suggestions and purchase-pattern analysis.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class PurchaseRecord(BaseModel):
    """A single purchase event."""

    product_id: str = Field(..., description="Unique product identifier")
    product_name: str = Field(default="", description="Human-readable product name")
    category: str = Field(default="", description="Product category")
    price: float = Field(default=0.0, ge=0.0, description="Purchase price")
    quantity: int = Field(default=1, ge=1, description="Quantity purchased")
    metadata: dict[str, Any] = Field(default_factory=dict)
    purchased_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PurchaseMemory:
    """Manages long-term purchase history for a user.

    Tracks purchase events to power recommendations, reorder
    suggestions, and spending-pattern analysis.
    """

    def __init__(self, user_id: str) -> None:
        self.user_id = user_id
        self._purchases: list[PurchaseRecord] = []

    async def record(
        self,
        product_id: str,
        *,
        product_name: str = "",
        category: str = "",
        price: float = 0.0,
        quantity: int = 1,
        metadata: dict[str, Any] | None = None,
    ) -> PurchaseRecord:
        """Record a new purchase event."""
        entry = PurchaseRecord(
            product_id=product_id,
            product_name=product_name,
            category=category,
            price=price,
            quantity=quantity,
            metadata=metadata or {},
        )
        self._purchases.append(entry)
        return entry

    async def get_history(
        self, *, limit: int | None = None
    ) -> list[PurchaseRecord]:
        """Return purchase history, most recent first."""
        sorted_purchases = sorted(
            self._purchases, key=lambda p: p.purchased_at, reverse=True
        )
        if limit is not None:
            return sorted_purchases[:limit]
        return sorted_purchases

    async def get_by_category(self, category: str) -> list[PurchaseRecord]:
        """Return purchases filtered by category."""
        return [p for p in self._purchases if p.category == category]

    async def get_by_product(self, product_id: str) -> list[PurchaseRecord]:
        """Return all purchase records for a specific product."""
        return [p for p in self._purchases if p.product_id == product_id]

    async def get_total_spend(self) -> float:
        """Calculate total spend across all purchases."""
        return sum(p.price * p.quantity for p in self._purchases)

    async def clear(self) -> None:
        """Clear all purchase history for the user."""
        self._purchases.clear()
