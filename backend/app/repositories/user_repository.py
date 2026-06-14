"""User repository — PostgreSQL data access for user entities.

Implements the repository pattern over SQLAlchemy AsyncSession,
providing typed CRUD operations for the User model.

Dependencies:
    - app.models.user.User
    - sqlalchemy.ext.asyncio.AsyncSession
"""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class UserRepositoryError(Exception):
    """Base exception for user repository operations."""


class UserNotFoundError(UserRepositoryError):
    """Raised when a user cannot be found."""


class UserAlreadyExistsError(UserRepositoryError):
    """Raised when a user with the same unique constraint already exists."""


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------


class UserRepository:
    """PostgreSQL data access for user accounts.

    Wraps an AsyncSession and exposes typed async CRUD operations
    following the repository pattern.

    Args:
        db: SQLAlchemy AsyncSession instance (injected via FastAPI Depends).
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    async def create(self, user: User) -> User:
        """Persist a new user to the database.

        Args:
            user: User model instance to insert.

        Returns:
            The persisted user with server-generated fields populated.

        Raises:
            UserAlreadyExistsError: If a user with the same email exists.
            UserRepositoryError: On unexpected database errors.
        """
        try:
            self._db.add(user)
            await self._db.commit()
            await self._db.refresh(user)
            logger.info("Created user id=%s email=%s", user.id, user.email)
            return user
        except IntegrityError as exc:
            await self._db.rollback()
            logger.warning("Duplicate user creation attempted: %s", exc)
            raise UserAlreadyExistsError(
                f"User with email '{user.email}' already exists"
            ) from exc
        except SQLAlchemyError as exc:
            await self._db.rollback()
            logger.error("Failed to create user: %s", exc)
            raise UserRepositoryError(f"Failed to create user: {exc}") from exc

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    async def get_by_id(self, user_id: UUID) -> User | None:
        """Retrieve a user by primary key.

        Args:
            user_id: UUID of the user.

        Returns:
            User instance or None if not found.
        """
        try:
            stmt = select(User).where(User.id == user_id)
            result = await self._db.execute(stmt)
            user = result.scalar_one_or_none()
            if user:
                logger.debug("Found user id=%s", user_id)
            else:
                logger.debug("User id=%s not found", user_id)
            return user
        except SQLAlchemyError as exc:
            logger.error("Failed to get user by id=%s: %s", user_id, exc)
            raise UserRepositoryError(
                f"Failed to retrieve user {user_id}"
            ) from exc

    async def get_by_email(self, email: str) -> User | None:
        """Retrieve a user by email address.

        Args:
            email: Unique email address.

        Returns:
            User instance or None if not found.
        """
        try:
            stmt = select(User).where(User.email == email)
            result = await self._db.execute(stmt)
            user = result.scalar_one_or_none()
            if user:
                logger.debug("Found user email=%s", email)
            else:
                logger.debug("User email=%s not found", email)
            return user
        except SQLAlchemyError as exc:
            logger.error("Failed to get user by email=%s: %s", email, exc)
            raise UserRepositoryError(
                f"Failed to retrieve user by email '{email}'"
            ) from exc

    async def list_all(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[User]:
        """List users with pagination.

        Args:
            limit: Maximum number of users to return.
            offset: Number of users to skip.

        Returns:
            List of User instances.
        """
        try:
            stmt = (
                select(User)
                .order_by(User.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await self._db.execute(stmt)
            users = list(result.scalars().all())
            logger.debug("Listed %d users (limit=%d, offset=%d)", len(users), limit, offset)
            return users
        except SQLAlchemyError as exc:
            logger.error("Failed to list users: %s", exc)
            raise UserRepositoryError("Failed to list users") from exc

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    async def update(self, user: User) -> User:
        """Commit pending changes on a user instance.

        The caller is expected to mutate the user object before calling
        this method. SQLAlchemy's unit-of-work will detect and flush the
        dirty attributes.

        Args:
            user: User model instance with modified attributes.

        Returns:
            The refreshed user with updated server-side fields.

        Raises:
            UserAlreadyExistsError: If update violates a unique constraint.
            UserRepositoryError: On unexpected database errors.
        """
        try:
            await self._db.commit()
            await self._db.refresh(user)
            logger.info("Updated user id=%s", user.id)
            return user
        except IntegrityError as exc:
            await self._db.rollback()
            logger.warning("Update violated constraint for user id=%s: %s", user.id, exc)
            raise UserAlreadyExistsError(
                f"Update failed — constraint violation: {exc}"
            ) from exc
        except SQLAlchemyError as exc:
            await self._db.rollback()
            logger.error("Failed to update user id=%s: %s", user.id, exc)
            raise UserRepositoryError(
                f"Failed to update user {user.id}"
            ) from exc

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    async def delete(self, user: User) -> None:
        """Delete a user from the database.

        Cascading deletes will remove related sessions, situations,
        and feedbacks as defined in the User model relationships.

        Args:
            user: User model instance to remove.

        Raises:
            UserRepositoryError: On unexpected database errors.
        """
        try:
            await self._db.delete(user)
            await self._db.commit()
            logger.info("Deleted user id=%s", user.id)
        except SQLAlchemyError as exc:
            await self._db.rollback()
            logger.error("Failed to delete user id=%s: %s", user.id, exc)
            raise UserRepositoryError(
                f"Failed to delete user {user.id}"
            ) from exc

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    async def count(self) -> int:
        """Return the total number of users."""
        try:
            stmt = select(func.count()).select_from(User)
            result = await self._db.execute(stmt)
            return result.scalar_one()
        except SQLAlchemyError as exc:
            logger.error("Failed to count users: %s", exc)
            raise UserRepositoryError("Failed to count users") from exc

    async def exists(self, user_id: UUID) -> bool:
        """Check whether a user exists by ID without loading the full entity."""
        try:
            stmt = select(func.count()).select_from(User).where(User.id == user_id)
            result = await self._db.execute(stmt)
            return result.scalar_one() > 0
        except SQLAlchemyError as exc:
            logger.error("Failed to check user existence id=%s: %s", user_id, exc)
            raise UserRepositoryError(
                f"Failed to check existence of user {user_id}"
            ) from exc

    async def save(self) -> None:
        """Flush and commit the current session."""
        try:
            await self._db.commit()
        except SQLAlchemyError as exc:
            await self._db.rollback()
            logger.error("Failed to save session: %s", exc)
            raise UserRepositoryError("Failed to save session") from exc
