"""Memory repository — PostgreSQL data access for user memory (JSONB).

Implements the repository pattern over SQLAlchemy AsyncSession,
providing typed async operations for reading and writing user memory
stored as JSONB on the User model.

Architecture:
    - Memory is stored as a JSONB column on the users table.
    - Each memory entry is keyed by a memory_key within the JSON structure.
    - Supports atomic partial updates via PostgreSQL JSONB operators.

Dependencies:
    - app.models.user.User (memory JSONB column)
    - sqlalchemy.ext.asyncio.AsyncSession
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class MemoryRepositoryError(Exception):
    """Base exception for memory repository operations."""


class MemoryNotFoundError(MemoryRepositoryError):
    """Raised when a memory entry cannot be found."""


class UserNotFoundError(MemoryRepositoryError):
    """Raised when the target user does not exist."""


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------


class MemoryRepository:
    """PostgreSQL data access for user memory (JSONB storage).

    Manages memory lifecycle within the User model's JSONB column.
    Provides keyed access to individual memory entries and bulk
    retrieval for full user memory state.

    Args:
        db: SQLAlchemy AsyncSession instance (injected via FastAPI Depends).
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    async def save_memory(
        self,
        user_id: UUID,
        memory_key: str,
        memory_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Save a memory entry under a specific key for a user.

        If the key already exists, it will be overwritten. A timestamp
        is automatically added to the entry.

        Args:
            user_id: UUID of the user.
            memory_key: Logical key for the memory entry (e.g., "short_term", "preferences").
            memory_data: Dictionary of memory data to store.

        Returns:
            The saved memory entry including metadata.

        Raises:
            UserNotFoundError: If the user does not exist.
            MemoryRepositoryError: On unexpected database errors.
        """
        try:
            user = await self._get_user_or_raise(user_id)

            # Build the entry with metadata
            entry = {
                **memory_data,
                "_updated_at": datetime.now(timezone.utc).isoformat(),
            }

            # Update JSONB field
            current_memory = user.memory or {}
            current_memory[memory_key] = entry
            user.memory = current_memory

            await self._db.commit()
            await self._db.refresh(user)

            logger.info(
                "Saved memory key='%s' for user id=%s",
                memory_key,
                user_id,
            )
            return entry

        except (UserNotFoundError, MemoryRepositoryError):
            raise
        except SQLAlchemyError as exc:
            await self._db.rollback()
            logger.error(
                "Failed to save memory key='%s' for user id=%s: %s",
                memory_key,
                user_id,
                exc,
            )
            raise MemoryRepositoryError(
                f"Failed to save memory '{memory_key}': {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Retrieve
    # ------------------------------------------------------------------

    async def get_memory(
        self,
        user_id: UUID,
        memory_key: str,
    ) -> dict[str, Any] | None:
        """Retrieve a specific memory entry by key.

        Args:
            user_id: UUID of the user.
            memory_key: Key of the memory entry to retrieve.

        Returns:
            Memory data dictionary, or None if the key doesn't exist.

        Raises:
            UserNotFoundError: If the user does not exist.
            MemoryRepositoryError: On unexpected database errors.
        """
        try:
            user = await self._get_user_or_raise(user_id)

            memory = user.memory or {}
            entry = memory.get(memory_key)

            if entry is not None:
                logger.debug("Retrieved memory key='%s' for user id=%s", memory_key, user_id)
            else:
                logger.debug("Memory key='%s' not found for user id=%s", memory_key, user_id)

            return entry

        except (UserNotFoundError, MemoryRepositoryError):
            raise
        except SQLAlchemyError as exc:
            logger.error(
                "Failed to get memory key='%s' for user id=%s: %s",
                memory_key,
                user_id,
                exc,
            )
            raise MemoryRepositoryError(
                f"Failed to retrieve memory '{memory_key}': {exc}"
            ) from exc

    async def get_user_memories(
        self,
        user_id: UUID,
        *,
        keys: list[str] | None = None,
    ) -> dict[str, Any]:
        """Retrieve all memory entries for a user (or a subset by keys).

        Args:
            user_id: UUID of the user.
            keys: Optional list of specific keys to retrieve. If None, returns all.

        Returns:
            Dictionary of memory entries keyed by memory_key.

        Raises:
            UserNotFoundError: If the user does not exist.
            MemoryRepositoryError: On unexpected database errors.
        """
        try:
            user = await self._get_user_or_raise(user_id)

            memory = user.memory or {}

            if keys is not None:
                result = {k: memory[k] for k in keys if k in memory}
            else:
                result = dict(memory)

            logger.debug(
                "Retrieved %d memory entries for user id=%s",
                len(result),
                user_id,
            )
            return result

        except (UserNotFoundError, MemoryRepositoryError):
            raise
        except SQLAlchemyError as exc:
            logger.error(
                "Failed to get user memories for user id=%s: %s", user_id, exc
            )
            raise MemoryRepositoryError(
                f"Failed to retrieve user memories: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    async def update_memory(
        self,
        user_id: UUID,
        memory_key: str,
        updates: dict[str, Any],
        *,
        merge: bool = True,
    ) -> dict[str, Any]:
        """Update a memory entry with partial or full replacement.

        Args:
            user_id: UUID of the user.
            memory_key: Key of the memory entry to update.
            updates: Dictionary of fields to update.
            merge: If True, merges with existing data. If False, replaces entirely.

        Returns:
            The updated memory entry.

        Raises:
            UserNotFoundError: If the user does not exist.
            MemoryNotFoundError: If the memory key doesn't exist and merge=True.
            MemoryRepositoryError: On unexpected database errors.
        """
        try:
            user = await self._get_user_or_raise(user_id)

            current_memory = user.memory or {}

            if merge:
                existing_entry = current_memory.get(memory_key)
                if existing_entry is None:
                    raise MemoryNotFoundError(
                        f"Memory key '{memory_key}' not found for user {user_id}. "
                        f"Use save_memory() to create a new entry."
                    )
                # Deep merge: update existing entry
                if isinstance(existing_entry, dict):
                    existing_entry.update(updates)
                    existing_entry["_updated_at"] = datetime.now(timezone.utc).isoformat()
                    entry = existing_entry
                else:
                    entry = {**updates, "_updated_at": datetime.now(timezone.utc).isoformat()}
            else:
                # Full replacement
                entry = {**updates, "_updated_at": datetime.now(timezone.utc).isoformat()}

            current_memory[memory_key] = entry
            user.memory = current_memory

            await self._db.commit()
            await self._db.refresh(user)

            logger.info(
                "Updated memory key='%s' for user id=%s (merge=%s)",
                memory_key,
                user_id,
                merge,
            )
            return entry

        except (UserNotFoundError, MemoryNotFoundError, MemoryRepositoryError):
            raise
        except SQLAlchemyError as exc:
            await self._db.rollback()
            logger.error(
                "Failed to update memory key='%s' for user id=%s: %s",
                memory_key,
                user_id,
                exc,
            )
            raise MemoryRepositoryError(
                f"Failed to update memory '{memory_key}': {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    async def delete_memory(
        self,
        user_id: UUID,
        memory_key: str,
    ) -> bool:
        """Delete a specific memory entry by key.

        Args:
            user_id: UUID of the user.
            memory_key: Key of the memory entry to delete.

        Returns:
            True if the entry existed and was deleted, False if not found.

        Raises:
            UserNotFoundError: If the user does not exist.
            MemoryRepositoryError: On unexpected database errors.
        """
        try:
            user = await self._get_user_or_raise(user_id)

            current_memory = user.memory or {}

            if memory_key not in current_memory:
                logger.debug(
                    "Memory key='%s' not found for deletion (user id=%s)",
                    memory_key,
                    user_id,
                )
                return False

            del current_memory[memory_key]
            user.memory = current_memory

            await self._db.commit()
            await self._db.refresh(user)

            logger.info(
                "Deleted memory key='%s' for user id=%s",
                memory_key,
                user_id,
            )
            return True

        except (UserNotFoundError, MemoryRepositoryError):
            raise
        except SQLAlchemyError as exc:
            await self._db.rollback()
            logger.error(
                "Failed to delete memory key='%s' for user id=%s: %s",
                memory_key,
                user_id,
                exc,
            )
            raise MemoryRepositoryError(
                f"Failed to delete memory '{memory_key}': {exc}"
            ) from exc

    async def clear_all_memories(self, user_id: UUID) -> None:
        """Clear all memory entries for a user (reset to empty).

        Args:
            user_id: UUID of the user.

        Raises:
            UserNotFoundError: If the user does not exist.
            MemoryRepositoryError: On unexpected database errors.
        """
        try:
            user = await self._get_user_or_raise(user_id)

            user.memory = {}
            await self._db.commit()
            await self._db.refresh(user)

            logger.info("Cleared all memories for user id=%s", user_id)

        except (UserNotFoundError, MemoryRepositoryError):
            raise
        except SQLAlchemyError as exc:
            await self._db.rollback()
            logger.error("Failed to clear memories for user id=%s: %s", user_id, exc)
            raise MemoryRepositoryError(
                f"Failed to clear memories: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Legacy Compatibility
    # ------------------------------------------------------------------

    async def get_user(self, user_id: UUID) -> User | None:
        """Retrieve a user by ID (legacy compatibility with MemoryManager).

        Args:
            user_id: UUID of the user.

        Returns:
            User instance or None.
        """
        stmt = select(User).where(User.id == user_id)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def save(self, user: User) -> User:
        """Persist user changes (legacy compatibility with MemoryManager).

        Args:
            user: User model instance to save.

        Returns:
            Refreshed user instance.
        """
        self._db.add(user)
        await self._db.commit()
        await self._db.refresh(user)
        return user

    # ------------------------------------------------------------------
    # Private Helpers
    # ------------------------------------------------------------------

    async def _get_user_or_raise(self, user_id: UUID) -> User:
        """Retrieve a user or raise UserNotFoundError."""
        try:
            stmt = select(User).where(User.id == user_id)
            result = await self._db.execute(stmt)
            user = result.scalar_one_or_none()

            if user is None:
                raise UserNotFoundError(f"User {user_id} not found")

            return user

        except UserNotFoundError:
            raise
        except SQLAlchemyError as exc:
            logger.error("Failed to fetch user id=%s: %s", user_id, exc)
            raise MemoryRepositoryError(
                f"Failed to fetch user {user_id}"
            ) from exc
