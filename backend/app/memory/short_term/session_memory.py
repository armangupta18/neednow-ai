from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.logger import logger

logger = logging.getLogger(__name__)


class InteractionLog(BaseModel):
    """Single interaction record in session memory."""

    model_config = ConfigDict(extra="forbid")

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_input: str = Field(..., min_length=1, description="User's input or query")
    assistant_response: str = Field(
        ..., min_length=1, description="Assistant's response"
    )
    interaction_type: str = Field(
        default="chat", description="Type of interaction (chat, search, recommend)"
    )
    metadata: dict = Field(
        default_factory=dict, description="Additional interaction context"
    )


class CartSnapshot(BaseModel):
    """Snapshot of cart state at a point in time."""

    model_config = ConfigDict(extra="forbid")

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    items_count: int = Field(default=0, ge=0)
    total_amount: float = Field(default=0.0, ge=0.0)
    items: list[dict] = Field(default_factory=list)


class UrgencyContext(BaseModel):
    """Current urgency context in the session."""

    model_config = ConfigDict(extra="forbid")

    level: str = Field(
        default="NORMAL",
        description="Urgency level (CRITICAL, HIGH, NORMAL, LOW)",
    )
    reason: str | None = None
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class SessionMemory(BaseModel):
    """Complete session-based short-term memory.

    Manages temporary context during a user session including interaction
    history, cart snapshots, current urgency, and contextual information
    that is session-specific and auto-expires after inactivity.
    """

    model_config = ConfigDict(extra="forbid")

    session_id: UUID
    user_id: UUID
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    interaction_history: list[InteractionLog] = Field(
        default_factory=list, max_length=50, description="Recent interactions (max 50)"
    )
    cart_snapshots: list[CartSnapshot] = Field(
        default_factory=list, max_length=5, description="Cart state history (max 5)"
    )
    current_urgency: UrgencyContext = Field(default_factory=UrgencyContext)
    current_category: str | None = None
    active_filters: dict = Field(default_factory=dict)
    session_notes: dict = Field(default_factory=dict)
    recommendation_context: dict = Field(default_factory=dict)
    is_active: bool = Field(default=True)
    session_duration_seconds: int = Field(default=0, ge=0)


class SessionMemoryManagerError(Exception):
    """Base exception for session memory errors."""

    pass


class SessionExpiredError(SessionMemoryManagerError):
    """Raised when session has expired."""

    pass


class SessionMemoryManager:
    """Manages session-based short-term memory for user interactions.

    Handles session lifecycle including creation, context management,
    interaction tracking, and automatic expiration. Provides a complete
    view of the current session state for agent reasoning.

    Architecture:
    - Manages interaction history during a session
    - Tracks cart state changes
    - Maintains urgency context
    - Supports category and recommendation context
    - Auto-expires on inactivity
    """

    # Session expiration after inactivity (seconds)
    SESSION_TIMEOUT_SECONDS = 3600  # 1 hour
    MAX_INTERACTIONS = 50
    MAX_CART_SNAPSHOTS = 5

    def __init__(self, session_id: UUID, user_id: UUID) -> None:
        """Initialize session memory manager.

        Args:
            session_id: Session identifier
            user_id: User identifier
        """
        self._session_id = session_id
        self._user_id = user_id
        self._logger = logger
        self._session_memory = SessionMemory(
            session_id=session_id,
            user_id=user_id,
        )

        self._logger.info(
            "Session memory initialized",
            extra={"session_id": str(session_id), "user_id": str(user_id)},
        )

    def add_interaction(
        self,
        user_input: str,
        assistant_response: str,
        interaction_type: str = "chat",
        metadata: dict | None = None,
    ) -> InteractionLog:
        """Add an interaction to session history.

        Args:
            user_input: User's input/query
            assistant_response: Assistant's response
            interaction_type: Type of interaction (chat, search, recommend)
            metadata: Optional additional context

        Returns:
            Added InteractionLog

        Raises:
            SessionExpiredError: If session has expired
        """
        self._check_session_active()

        self._logger.debug(
            "Adding interaction to session",
            extra={
                "session_id": str(self._session_id),
                "input_length": len(user_input),
                "interaction_type": interaction_type,
            },
        )

        interaction = InteractionLog(
            user_input=user_input,
            assistant_response=assistant_response,
            interaction_type=interaction_type,
            metadata=metadata or {},
        )

        self._session_memory.interaction_history.append(interaction)

        # Keep only latest interactions
        if len(self._session_memory.interaction_history) > self.MAX_INTERACTIONS:
            self._session_memory.interaction_history = (
                self._session_memory.interaction_history[-self.MAX_INTERACTIONS :]
            )

        self._update_activity()

        self._logger.debug(
            "Interaction added",
            extra={
                "session_id": str(self._session_id),
                "total_interactions": len(self._session_memory.interaction_history),
            },
        )

        return interaction

    def snapshot_cart_state(
        self,
        items_count: int,
        total_amount: float,
        items: list[dict] | None = None,
    ) -> CartSnapshot:
        """Create a snapshot of cart state.

        Args:
            items_count: Number of items in cart
            total_amount: Cart total
            items: Optional full item list

        Returns:
            CartSnapshot

        Raises:
            SessionExpiredError: If session has expired
        """
        self._check_session_active()

        self._logger.debug(
            "Creating cart snapshot",
            extra={
                "session_id": str(self._session_id),
                "items": items_count,
                "total": total_amount,
            },
        )

        snapshot = CartSnapshot(
            items_count=items_count,
            total_amount=total_amount,
            items=items or [],
        )

        self._session_memory.cart_snapshots.append(snapshot)

        # Keep only latest snapshots
        if len(self._session_memory.cart_snapshots) > self.MAX_CART_SNAPSHOTS:
            self._session_memory.cart_snapshots = (
                self._session_memory.cart_snapshots[-self.MAX_CART_SNAPSHOTS :]
            )

        self._update_activity()

        return snapshot

    def update_urgency_context(
        self,
        level: str,
        reason: str | None = None,
        confidence: float = 0.5,
    ) -> UrgencyContext:
        """Update current urgency context.

        Args:
            level: Urgency level (CRITICAL, HIGH, NORMAL, LOW)
            reason: Optional explanation
            confidence: Confidence score (0-1)

        Returns:
            Updated UrgencyContext

        Raises:
            SessionExpiredError: If session has expired
        """
        self._check_session_active()

        self._logger.debug(
            "Updating urgency context",
            extra={
                "session_id": str(self._session_id),
                "level": level,
                "confidence": confidence,
            },
        )

        self._session_memory.current_urgency = UrgencyContext(
            level=level,
            reason=reason,
            confidence=confidence,
        )

        self._update_activity()

        return self._session_memory.current_urgency

    def set_category_context(
        self,
        category: str,
    ) -> None:
        """Set current product category context.

        Args:
            category: Product category
        """
        self._check_session_active()

        self._logger.debug(
            "Setting category context",
            extra={"session_id": str(self._session_id), "category": category},
        )

        self._session_memory.current_category = category
        self._update_activity()

    def update_filters(
        self,
        filters: dict,
        merge: bool = True,
    ) -> dict:
        """Update active filters.

        Args:
            filters: Filters dictionary
            merge: If True, merge with existing filters; if False, replace

        Returns:
            Current filters
        """
        self._check_session_active()

        self._logger.debug(
            "Updating filters",
            extra={
                "session_id": str(self._session_id),
                "filter_keys": list(filters.keys()),
                "merge": merge,
            },
        )

        if merge:
            self._session_memory.active_filters.update(filters)
        else:
            self._session_memory.active_filters = filters

        self._update_activity()

        return self._session_memory.active_filters

    def add_session_note(
        self,
        key: str,
        value: Any,
    ) -> None:
        """Add a session note for contextual information.

        Args:
            key: Note key
            value: Note value
        """
        self._check_session_active()

        self._logger.debug(
            "Adding session note",
            extra={"session_id": str(self._session_id), "key": key},
        )

        self._session_memory.session_notes[key] = value
        self._update_activity()

    def update_recommendation_context(
        self,
        context: dict,
    ) -> dict:
        """Update recommendation context.

        Args:
            context: Recommendation context data

        Returns:
            Updated recommendation context
        """
        self._check_session_active()

        self._logger.debug(
            "Updating recommendation context",
            extra={
                "session_id": str(self._session_id),
                "context_keys": list(context.keys()),
            },
        )

        self._session_memory.recommendation_context.update(context)
        self._update_activity()

        return self._session_memory.recommendation_context

    def get_recent_interactions(
        self,
        limit: int = 10,
    ) -> list[InteractionLog]:
        """Get recent interactions.

        Args:
            limit: Maximum number of interactions to return

        Returns:
            List of recent InteractionLog entries
        """
        return self._session_memory.interaction_history[-limit:]

    def get_interaction_summary(self) -> str:
        """Generate summary of session interactions.

        Returns:
            Formatted interaction summary
        """
        if not self._session_memory.interaction_history:
            return "No interactions in this session."

        summary_parts = []
        for idx, interaction in enumerate(
            self._session_memory.interaction_history[-5:], 1
        ):
            summary_parts.append(f"{idx}. User: {interaction.user_input[:50]}")

        return "\n".join(summary_parts)

    def get_session_context(self) -> str:
        """Generate comprehensive session context string.

        Combines interaction history, current urgency, category,
        and other session-specific context for agent reasoning.

        Returns:
            Formatted session context string

        Note:
            Future: Integrate with embeddings for semantic matching
            against historical sessions for pattern recognition.
        """
        context_parts = []

        # Session metadata
        context_parts.append(f"Session Duration: {self._session_memory.session_duration_seconds}s")

        # Current context
        if self._session_memory.current_category:
            context_parts.append(f"Category: {self._session_memory.current_category}")

        if self._session_memory.current_urgency.level != "NORMAL":
            urgency_str = f"Urgency: {self._session_memory.current_urgency.level}"
            if self._session_memory.current_urgency.reason:
                urgency_str += f" ({self._session_memory.current_urgency.reason})"
            context_parts.append(urgency_str)

        # Active filters
        if self._session_memory.active_filters:
            filters_str = ", ".join(
                f"{k}={v}" for k, v in self._session_memory.active_filters.items()
            )
            context_parts.append(f"Filters: {filters_str}")

        # Recent interactions summary
        if self._session_memory.interaction_history:
            context_parts.append("Recent Interactions:")
            for interaction in self._session_memory.interaction_history[-3:]:
                context_parts.append(f"  - {interaction.user_input[:40]}")

        # Cart state
        if self._session_memory.cart_snapshots:
            latest_cart = self._session_memory.cart_snapshots[-1]
            context_parts.append(
                f"Cart: {latest_cart.items_count} items, ${latest_cart.total_amount:.2f}"
            )

        return "\n".join(context_parts)

    def get_memory_state(self) -> SessionMemory:
        """Get current session memory state.

        Returns:
            Complete SessionMemory object

        Raises:
            SessionExpiredError: If session has expired
        """
        self._check_session_active()
        return self._session_memory.model_copy()

    def check_session_expired(self) -> bool:
        """Check if session has expired due to inactivity.

        Returns:
            True if session has expired, False otherwise
        """
        elapsed = datetime.now(timezone.utc) - self._session_memory.last_activity_at
        is_expired = elapsed.total_seconds() > self.SESSION_TIMEOUT_SECONDS

        if is_expired:
            self._logger.info(
                "Session expired due to inactivity",
                extra={
                    "session_id": str(self._session_id),
                    "inactivity_seconds": elapsed.total_seconds(),
                },
            )
            self._session_memory.is_active = False

        return is_expired

    def refresh_session_timeout(self) -> None:
        """Refresh session timeout by updating last activity.

        Resets the inactivity timer without changing other session state.
        """
        self._update_activity()
        self._logger.debug(
            "Session timeout refreshed",
            extra={"session_id": str(self._session_id)},
        )

    def end_session(self) -> None:
        """Explicitly end the session.

        Marks session as inactive and finalizes session duration.
        """
        self._session_memory.is_active = False
        self._session_memory.session_duration_seconds = int(
            (datetime.now(timezone.utc) - self._session_memory.created_at).total_seconds()
        )

        self._logger.info(
            "Session ended",
            extra={
                "session_id": str(self._session_id),
                "duration_seconds": self._session_memory.session_duration_seconds,
                "interactions": len(self._session_memory.interaction_history),
            },
        )

    def _check_session_active(self) -> None:
        """Check if session is still active.

        Raises:
            SessionExpiredError: If session is expired
        """
        if self.check_session_expired():
            self._logger.warning(
                "Attempted to access expired session",
                extra={"session_id": str(self._session_id)},
            )
            raise SessionExpiredError(
                f"Session {self._session_id} has expired due to inactivity"
            )

        if not self._session_memory.is_active:
            raise SessionExpiredError(f"Session {self._session_id} is not active")

    def _update_activity(self) -> None:
        """Update last activity timestamp."""
        self._session_memory.last_activity_at = datetime.now(timezone.utc)

        # Update session duration
        self._session_memory.session_duration_seconds = int(
            (self._session_memory.last_activity_at - self._session_memory.created_at).total_seconds()
        )

    def export_session_data(self) -> dict:
        """Export complete session data for archival or analysis.

        Returns:
            Dictionary representation of session memory

        Note:
            Future: This data could be used for:
            - Session analytics and user behavior analysis
            - FAISS-based similarity search for pattern recognition
            - Long-term learning and model improvements
            - User journey analytics
        """
        return self._session_memory.model_dump()

    def to_compact_form(self) -> dict:
        """Get compact session summary for quick access.

        Useful for logging, caching, or quick status checks.

        Returns:
            Compact session summary
        """
        return {
            "session_id": str(self._session_id),
            "user_id": str(self._user_id),
            "is_active": self._session_memory.is_active,
            "duration_seconds": self._session_memory.session_duration_seconds,
            "interactions": len(self._session_memory.interaction_history),
            "last_activity": self._session_memory.last_activity_at.isoformat(),
            "current_category": self._session_memory.current_category,
            "urgency_level": self._session_memory.current_urgency.level,
            "cart_items": (
                self._session_memory.cart_snapshots[-1].items_count
                if self._session_memory.cart_snapshots
                else 0
            ),
        }
