"""Long-term behavior memory module.

Stores and retrieves behavioral signals (views, clicks, searches, etc.)
to build a persistent understanding of user engagement patterns.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class BehaviorType(str, Enum):
    """Supported behavior event types."""

    VIEW = "view"
    CLICK = "click"
    SEARCH = "search"
    ADD_TO_CART = "add_to_cart"
    WISHLIST = "wishlist"
    REVIEW = "review"
    SHARE = "share"
    COMPARE = "compare"


class BehaviorEvent(BaseModel):
    """A single recorded user behavior event."""

    behavior_type: BehaviorType = Field(..., description="Type of behavior")
    target_id: str = Field(default="", description="ID of the target entity")
    target_name: str = Field(default="", description="Human-readable target name")
    context: dict[str, Any] = Field(
        default_factory=dict, description="Additional event context"
    )
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BehaviorMemory:
    """Manages long-term behavioral signal storage and retrieval.

    Captures user engagement events over time to enable
    interest profiling, trend detection, and behavioral scoring.
    """

    def __init__(self, user_id: str) -> None:
        self.user_id = user_id
        self._events: list[BehaviorEvent] = []

    async def record(
        self,
        behavior_type: BehaviorType | str,
        *,
        target_id: str = "",
        target_name: str = "",
        context: dict[str, Any] | None = None,
    ) -> BehaviorEvent:
        """Record a new behavior event."""
        if isinstance(behavior_type, str):
            behavior_type = BehaviorType(behavior_type)

        event = BehaviorEvent(
            behavior_type=behavior_type,
            target_id=target_id,
            target_name=target_name,
            context=context or {},
        )
        self._events.append(event)
        return event

    async def get_events(
        self,
        *,
        behavior_type: BehaviorType | str | None = None,
        limit: int | None = None,
    ) -> list[BehaviorEvent]:
        """Retrieve behavior events, optionally filtered by type."""
        events = self._events

        if behavior_type is not None:
            if isinstance(behavior_type, str):
                behavior_type = BehaviorType(behavior_type)
            events = [e for e in events if e.behavior_type == behavior_type]

        # Most recent first
        events = sorted(events, key=lambda e: e.timestamp, reverse=True)

        if limit is not None:
            return events[:limit]
        return events

    async def get_frequent_targets(
        self, *, top_n: int = 10
    ) -> list[tuple[str, int]]:
        """Return the most frequently interacted-with target IDs."""
        counts: dict[str, int] = {}
        for event in self._events:
            if event.target_id:
                counts[event.target_id] = counts.get(event.target_id, 0) + 1

        sorted_targets = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_targets[:top_n]

    async def get_event_count(
        self, behavior_type: BehaviorType | str | None = None
    ) -> int:
        """Return the total number of recorded events, optionally by type."""
        if behavior_type is None:
            return len(self._events)

        if isinstance(behavior_type, str):
            behavior_type = BehaviorType(behavior_type)
        return sum(1 for e in self._events if e.behavior_type == behavior_type)

    async def clear(self) -> None:
        """Clear all behavior events for the user."""
        self._events.clear()
