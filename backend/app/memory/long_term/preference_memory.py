"""Long-term preference memory module.

Stores and retrieves user preferences learned over time,
such as brand affinity, category preferences, price sensitivity, etc.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class PreferenceEntry(BaseModel):
    """A single learned user preference."""

    key: str = Field(..., description="Preference identifier (e.g. 'brand_affinity')")
    value: Any = Field(..., description="Preference value")
    confidence: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Confidence score for this preference"
    )
    source: str = Field(
        default="inferred", description="How the preference was learned"
    )
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PreferenceMemory:
    """Manages long-term user preference storage and retrieval.

    Tracks evolving user preferences across sessions, enabling
    personalized product recommendations and search refinement.
    """

    def __init__(self, user_id: str) -> None:
        self.user_id = user_id
        self._preferences: dict[str, PreferenceEntry] = {}

    async def store(
        self,
        key: str,
        value: Any,
        *,
        confidence: float = 0.5,
        source: str = "inferred",
    ) -> PreferenceEntry:
        """Store or update a user preference."""
        entry = PreferenceEntry(
            key=key,
            value=value,
            confidence=confidence,
            source=source,
        )
        self._preferences[key] = entry
        return entry

    async def retrieve(self, key: str) -> PreferenceEntry | None:
        """Retrieve a specific preference by key."""
        return self._preferences.get(key)

    async def retrieve_all(self) -> list[PreferenceEntry]:
        """Retrieve all stored preferences for the user."""
        return list(self._preferences.values())

    async def retrieve_by_confidence(
        self, min_confidence: float = 0.7
    ) -> list[PreferenceEntry]:
        """Retrieve preferences above a confidence threshold."""
        return [
            entry
            for entry in self._preferences.values()
            if entry.confidence >= min_confidence
        ]

    async def remove(self, key: str) -> bool:
        """Remove a preference. Returns True if it existed."""
        return self._preferences.pop(key, None) is not None

    async def clear(self) -> None:
        """Clear all preferences for the user."""
        self._preferences.clear()
