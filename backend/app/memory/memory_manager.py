from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.logger import logger
from app.memory.memory_repository import MemoryRepository
from app.memory.schemas import UserMemory

logger = logging.getLogger(__name__)


class ShortTermMemory(BaseModel):
    """Short-term memory with automatic expiration.

    Stores temporary context like current session state, recent interactions,
    and contextual information that decays over time.
    """

    model_config = ConfigDict(extra="forbid")

    session_context: dict = Field(default_factory=dict)
    recent_queries: list[str] = Field(default_factory=list, max_length=10)
    current_cart_state: dict = Field(default_factory=dict)
    last_interaction_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    interaction_count: int = Field(default=0, ge=0)
    active_urgency_level: str | None = None


class LongTermMemory(BaseModel):
    """Long-term memory for persistent user profile information.

    Stores preferences, purchase history, behavioral patterns, and
    sustainability profile that persists across sessions.
    """

    model_config = ConfigDict(extra="forbid")

    dietary_preferences: list[str] = Field(default_factory=list)
    preferred_brands: list[str] = Field(default_factory=list)
    budget_level: str | None = None
    family_size: int | None = None
    purchase_patterns: list[str] = Field(default_factory=list)
    sustainability_score: float = Field(default=0.0, ge=0.0, le=100.0)
    total_purchases: int = Field(default=0, ge=0)
    favorite_categories: list[str] = Field(default_factory=list)
    past_urgency_patterns: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MemoryState(BaseModel):
    """Complete memory state combining short and long-term memory."""

    model_config = ConfigDict(extra="forbid")

    user_id: UUID
    short_term: ShortTermMemory = Field(default_factory=ShortTermMemory)
    long_term: LongTermMemory = Field(default_factory=LongTermMemory)
    metadata: dict = Field(default_factory=dict)


class MemoryManagerError(Exception):
    """Base exception for memory manager errors."""

    pass


class MemoryNotFoundError(MemoryManagerError):
    """Raised when memory is not found."""

    pass


class MemoryValidationError(MemoryManagerError):
    """Raised when memory validation fails."""

    pass


class MemoryManager:
    """Orchestrates user memory management across short-term and long-term storage.

    Manages memory lifecycle including creation, retrieval, updates, decay,
    and provides memory context for agent reasoning. Supports both session-based
    short-term memory and persistent long-term user profiles.

    Architecture:
    - Short-term memory: Session context, recent interactions (auto-expiring)
    - Long-term memory: User preferences, purchase history, behavioral patterns
    - Embeddings: Future FAISS integration for semantic memory retrieval
    """

    # Short-term memory expiration in seconds
    SHORT_TERM_EXPIRY_SECONDS = 3600  # 1 hour
    MAX_RECENT_QUERIES = 10
    MAX_SESSION_CONTEXT_SIZE = 20

    def __init__(self, repository: MemoryRepository) -> None:
        self._repository = repository
        self._logger = logger

    async def initialize_user_memory(
        self,
        user_id: UUID,
        initial_preferences: dict | None = None,
    ) -> MemoryState:
        """Initialize memory for a new user.

        Args:
            user_id: User identifier
            initial_preferences: Optional initial preference data

        Returns:
            Initialized MemoryState

        Raises:
            MemoryManagerError: If initialization fails
        """
        self._logger.info(
            "Initializing user memory",
            extra={"user_id": str(user_id)},
        )

        try:
            user = await self._repository.get_user(user_id)
            if not user:
                self._logger.warning(
                    "User not found during memory initialization",
                    extra={"user_id": str(user_id)},
                )
                raise MemoryNotFoundError(f"User {user_id} not found")

            # Initialize long-term memory with preferences
            long_term_data = initial_preferences or {}
            long_term = LongTermMemory(**long_term_data)

            # Create memory state
            memory_state = MemoryState(
                user_id=user_id,
                long_term=long_term,
            )

            # Save to user
            user.memory = memory_state.model_dump()
            await self._repository.save(user)

            self._logger.info(
                "User memory initialized",
                extra={"user_id": str(user_id)},
            )

            return memory_state

        except MemoryNotFoundError:
            raise
        except Exception as exc:
            self._logger.error(
                "Memory initialization failed",
                extra={"user_id": str(user_id), "error": str(exc)},
            )
            raise MemoryManagerError(f"Failed to initialize memory: {str(exc)}") from exc

    async def retrieve_memory(
        self,
        user_id: UUID,
    ) -> UserMemory:
        """Retrieve user memory as UserMemory schema (legacy compatibility).

        If the user does not exist, returns an empty UserMemory without
        raising an exception — the supervisor continues with defaults.

        Args:
            user_id: User identifier

        Returns:
            UserMemory object (empty if user not found)
        """
        self._logger.debug(
            "Retrieving user memory",
            extra={"user_id": str(user_id)},
        )

        try:
            user = await self._repository.get_user(user_id)
            if not user:
                # No user record — return empty memory, log at DEBUG only
                self._logger.debug(
                    "No memory found for user, returning empty result",
                    extra={"user_id": str(user_id)},
                )
                return UserMemory()

            memory_data = user.memory or {}
            return UserMemory(**memory_data)

        except Exception as exc:
            self._logger.error(
                "Memory retrieval failed",
                extra={"user_id": str(user_id), "error": str(exc)},
            )
            # Return empty memory so the pipeline can continue
            return UserMemory()

    async def get_memory_state(
        self,
        user_id: UUID,
    ) -> MemoryState:
        """Retrieve complete memory state with short and long-term memory.

        Args:
            user_id: User identifier

        Returns:
            Complete MemoryState

        Raises:
            MemoryNotFoundError: If user not found
            MemoryValidationError: If memory data is invalid
        """
        self._logger.debug(
            "Retrieving complete memory state",
            extra={"user_id": str(user_id)},
        )

        try:
            user = await self._repository.get_user(user_id)
            if not user:
                self._logger.warning(
                    "User not found",
                    extra={"user_id": str(user_id)},
                )
                raise MemoryNotFoundError(f"User {user_id} not found")

            memory_data = user.memory or {}

            if not memory_data:
                return MemoryState(user_id=user_id)

            # Parse memory state
            memory_state = MemoryState(user_id=user_id, **memory_data)

            # Check and apply short-term memory decay
            memory_state = self._apply_memory_decay(memory_state)

            self._logger.debug(
                "Memory state retrieved",
                extra={
                    "user_id": str(user_id),
                    "has_short_term": bool(memory_state.short_term.session_context),
                },
            )

            return memory_state

        except (MemoryNotFoundError, MemoryValidationError):
            raise
        except Exception as exc:
            self._logger.error(
                "Memory state retrieval failed",
                extra={"user_id": str(user_id), "error": str(exc)},
            )
            raise MemoryManagerError(
                f"Failed to get memory state: {str(exc)}"
            ) from exc

    async def save_memory(
        self,
        user_id: UUID,
        memory: UserMemory,
    ) -> dict:
        """Save user memory (legacy compatibility).

        Args:
            user_id: User identifier
            memory: UserMemory object

        Returns:
            Saved memory dictionary

        Raises:
            MemoryNotFoundError: If user not found
        """
        self._logger.info(
            "Saving user memory",
            extra={"user_id": str(user_id)},
        )

        try:
            user = await self._repository.get_user(user_id)
            if not user:
                self._logger.warning(
                    "User not found during memory save",
                    extra={"user_id": str(user_id)},
                )
                raise MemoryNotFoundError(f"User {user_id} not found")

            user.memory = memory.model_dump()
            await self._repository.save(user)

            self._logger.info(
                "User memory saved",
                extra={"user_id": str(user_id)},
            )

            return user.memory

        except MemoryNotFoundError:
            raise
        except Exception as exc:
            self._logger.error(
                "Memory save failed",
                extra={"user_id": str(user_id), "error": str(exc)},
            )
            raise MemoryManagerError(f"Failed to save memory: {str(exc)}") from exc

    async def update_memory(
        self,
        user_id: UUID,
        updates: dict,
    ) -> UserMemory:
        """Update user memory with partial updates.

        Args:
            user_id: User identifier
            updates: Dictionary of fields to update

        Returns:
            Updated UserMemory object

        Raises:
            MemoryNotFoundError: If user not found
            MemoryValidationError: If updates are invalid
        """
        self._logger.info(
            "Updating user memory",
            extra={"user_id": str(user_id), "update_fields": list(updates.keys())},
        )

        try:
            user = await self._repository.get_user(user_id)
            if not user:
                self._logger.warning(
                    "User not found during memory update",
                    extra={"user_id": str(user_id)},
                )
                raise MemoryNotFoundError(f"User {user_id} not found")

            existing = user.memory or {}
            existing.update(updates)

            # Validate updated memory
            try:
                user_memory = UserMemory(**existing)
            except Exception as exc:
                self._logger.warning(
                    "Memory validation failed during update",
                    extra={"user_id": str(user_id), "error": str(exc)},
                )
                raise MemoryValidationError(f"Invalid memory updates: {str(exc)}") from exc

            user.memory = existing
            await self._repository.save(user)

            self._logger.info(
                "User memory updated",
                extra={"user_id": str(user_id)},
            )

            return user_memory

        except (MemoryNotFoundError, MemoryValidationError):
            raise
        except Exception as exc:
            self._logger.error(
                "Memory update failed",
                extra={"user_id": str(user_id), "error": str(exc)},
            )
            raise MemoryManagerError(f"Failed to update memory: {str(exc)}") from exc

    async def update_memory_state(
        self,
        user_id: UUID,
        memory_state: MemoryState,
    ) -> MemoryState:
        """Update complete memory state.

        Args:
            user_id: User identifier
            memory_state: New memory state

        Returns:
            Updated MemoryState

        Raises:
            MemoryNotFoundError: If user not found
        """
        self._logger.debug(
            "Updating memory state",
            extra={"user_id": str(user_id)},
        )

        try:
            user = await self._repository.get_user(user_id)
            if not user:
                raise MemoryNotFoundError(f"User {user_id} not found")

            user.memory = memory_state.model_dump()
            await self._repository.save(user)

            self._logger.debug(
                "Memory state updated",
                extra={"user_id": str(user_id)},
            )

            return memory_state

        except MemoryNotFoundError:
            raise
        except Exception as exc:
            self._logger.error(
                "Memory state update failed",
                extra={"user_id": str(user_id), "error": str(exc)},
            )
            raise MemoryManagerError(f"Failed to update memory state: {str(exc)}") from exc

    async def add_short_term_context(
        self,
        user_id: UUID,
        context_key: str,
        context_value: Any,
    ) -> None:
        """Add to short-term session context.

        Args:
            user_id: User identifier
            context_key: Context key
            context_value: Context value

        Raises:
            MemoryNotFoundError: If user not found
        """
        self._logger.debug(
            "Adding short-term context",
            extra={"user_id": str(user_id), "key": context_key},
        )

        try:
            memory_state = await self.get_memory_state(user_id)

            if len(memory_state.short_term.session_context) >= self.MAX_SESSION_CONTEXT_SIZE:
                memory_state.short_term.session_context.pop(
                    next(iter(memory_state.short_term.session_context))
                )

            memory_state.short_term.session_context[context_key] = context_value
            memory_state.short_term.last_interaction_timestamp = datetime.now(timezone.utc)
            memory_state.short_term.interaction_count += 1

            await self.update_memory_state(user_id, memory_state)

        except Exception as exc:
            self._logger.error(
                "Failed to add short-term context",
                extra={"user_id": str(user_id), "key": context_key, "error": str(exc)},
            )
            raise

    async def add_recent_query(
        self,
        user_id: UUID,
        query: str,
    ) -> None:
        """Add recent query to short-term memory.

        Args:
            user_id: User identifier
            query: Query text
        """
        self._logger.debug(
            "Adding recent query",
            extra={"user_id": str(user_id), "query_length": len(query)},
        )

        try:
            memory_state = await self.get_memory_state(user_id)

            memory_state.short_term.recent_queries.insert(0, query)
            if len(memory_state.short_term.recent_queries) > self.MAX_RECENT_QUERIES:
                memory_state.short_term.recent_queries = (
                    memory_state.short_term.recent_queries[: self.MAX_RECENT_QUERIES]
                )

            await self.update_memory_state(user_id, memory_state)

        except Exception as exc:
            self._logger.error(
                "Failed to add recent query",
                extra={"user_id": str(user_id), "error": str(exc)},
            )

    async def update_long_term_memory(
        self,
        user_id: UUID,
        updates: dict,
    ) -> LongTermMemory:
        """Update long-term memory preferences.

        Args:
            user_id: User identifier
            updates: Fields to update

        Returns:
            Updated LongTermMemory

        Raises:
            MemoryNotFoundError: If user not found
        """
        self._logger.info(
            "Updating long-term memory",
            extra={"user_id": str(user_id), "fields": list(updates.keys())},
        )

        try:
            memory_state = await self.get_memory_state(user_id)

            # Update long-term memory
            long_term_data = memory_state.long_term.model_dump()
            long_term_data.update(updates)
            long_term_data["last_updated_at"] = datetime.now(timezone.utc)

            memory_state.long_term = LongTermMemory(**long_term_data)

            await self.update_memory_state(user_id, memory_state)

            self._logger.info(
                "Long-term memory updated",
                extra={"user_id": str(user_id)},
            )

            return memory_state.long_term

        except Exception as exc:
            self._logger.error(
                "Failed to update long-term memory",
                extra={"user_id": str(user_id), "error": str(exc)},
            )
            raise

    async def clear_short_term_memory(
        self,
        user_id: UUID,
    ) -> None:
        """Clear short-term memory (session context, recent queries).

        Args:
            user_id: User identifier
        """
        self._logger.info(
            "Clearing short-term memory",
            extra={"user_id": str(user_id)},
        )

        try:
            memory_state = await self.get_memory_state(user_id)
            memory_state.short_term = ShortTermMemory()
            await self.update_memory_state(user_id, memory_state)

        except Exception as exc:
            self._logger.error(
                "Failed to clear short-term memory",
                extra={"user_id": str(user_id), "error": str(exc)},
            )

    def _apply_memory_decay(
        self,
        memory_state: MemoryState,
    ) -> MemoryState:
        """Apply time-based decay to short-term memory.

        Checks if short-term memory has expired and clears if necessary.

        Args:
            memory_state: Current memory state

        Returns:
            Memory state with decay applied
        """
        if not memory_state.short_term.last_interaction_timestamp:
            return memory_state

        elapsed = datetime.now(timezone.utc) - memory_state.short_term.last_interaction_timestamp

        if elapsed.total_seconds() > self.SHORT_TERM_EXPIRY_SECONDS:
            self._logger.debug(
                "Short-term memory expired",
                extra={
                    "user_id": str(memory_state.user_id),
                    "elapsed_seconds": elapsed.total_seconds(),
                },
            )
            memory_state.short_term = ShortTermMemory()

        return memory_state

    def get_memory_context(
        self,
        memory_state: MemoryState,
    ) -> str:
        """Generate text context from memory for agent reasoning.

        Args:
            memory_state: Current memory state

        Returns:
            Formatted memory context string

        Note:
            Future: Integrate with embeddings for semantic memory retrieval
            and FAISS-based similarity search.
        """
        sections = []

        # Long-term preferences
        if memory_state.long_term.dietary_preferences:
            sections.append(
                f"Dietary Preferences: {', '.join(memory_state.long_term.dietary_preferences)}"
            )

        if memory_state.long_term.preferred_brands:
            sections.append(
                f"Preferred Brands: {', '.join(memory_state.long_term.preferred_brands)}"
            )

        if memory_state.long_term.budget_level:
            sections.append(f"Budget Level: {memory_state.long_term.budget_level}")

        if memory_state.long_term.family_size:
            sections.append(f"Family Size: {memory_state.long_term.family_size}")

        if memory_state.long_term.favorite_categories:
            sections.append(
                f"Favorite Categories: {', '.join(memory_state.long_term.favorite_categories)}"
            )

        sections.append(
            f"Sustainability Score: {memory_state.long_term.sustainability_score}"
        )

        # Short-term context
        if memory_state.short_term.active_urgency_level:
            sections.append(f"Current Urgency: {memory_state.short_term.active_urgency_level}")

        if memory_state.short_term.recent_queries:
            sections.append(
                f"Recent Queries: {'; '.join(memory_state.short_term.recent_queries[:3])}"
            )

        return "\n".join(sections)
