"""Recommendation repository — PostgreSQL data access for recommendation history.

Implements the repository pattern over SQLAlchemy AsyncSession,
providing typed async operations for saving, retrieving, and analyzing
product recommendations.

Architecture:
    - Recommendations are stored in a dedicated table.
    - Each recommendation record links to a user and optionally a situation.
    - Supports full history retrieval and analytics queries.

Dependencies:
    - app.models.recommendation.Recommendation
    - sqlalchemy.ext.asyncio.AsyncSession
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    select,
    func,
    desc,
)
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recommendation import Recommendation
from app.models.user import User

logger = logging.getLogger(__name__)# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class RecommendationRepositoryError(Exception):
    """Base exception for recommendation repository operations."""


class RecommendationNotFoundError(RecommendationRepositoryError):
    """Raised when a recommendation record cannot be found."""


class UserNotFoundError(RecommendationRepositoryError):
    """Raised when the target user does not exist."""


# ---------------------------------------------------------------------------
# Analytics Result
# ---------------------------------------------------------------------------


class RecommendationAnalytics:
    """Container for recommendation analytics data."""

    def __init__(
        self,
        total_recommendations: int = 0,
        avg_confidence: float = 0.0,
        avg_items_per_recommendation: float = 0.0,
        top_categories: list[dict[str, Any]] | None = None,
        recommendations_by_urgency: dict[str, int] | None = None,
        recent_count_7d: int = 0,
        recent_count_30d: int = 0,
    ) -> None:
        self.total_recommendations = total_recommendations
        self.avg_confidence = avg_confidence
        self.avg_items_per_recommendation = avg_items_per_recommendation
        self.top_categories = top_categories or []
        self.recommendations_by_urgency = recommendations_by_urgency or {}
        self.recent_count_7d = recent_count_7d
        self.recent_count_30d = recent_count_30d

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_recommendations": self.total_recommendations,
            "avg_confidence": round(self.avg_confidence, 3),
            "avg_items_per_recommendation": round(self.avg_items_per_recommendation, 1),
            "top_categories": self.top_categories,
            "recommendations_by_urgency": self.recommendations_by_urgency,
            "recent_count_7d": self.recent_count_7d,
            "recent_count_30d": self.recent_count_30d,
        }


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------


class RecommendationRepository:
    """PostgreSQL data access for recommendation history and analytics.

    Persists generated recommendations for history, replay, and analytics.
    Supports user-level and system-level queries.

    Args:
        db: SQLAlchemy AsyncSession instance (injected via FastAPI Depends).
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    async def save_recommendation(
        self,
        user_id: str,
        session_id: str,
        product_id: str,
        product_name: str,
        score: float,
        reason: str,
        agent_source: str,
    ) -> Recommendation:
        """Persist a recommendation result.

        Args:
            user_id: User who received the recommendation.
            session_id: Session in which the recommendation was made.
            product_id: Recommended product ID.
            product_name: Product title.
            score: Ranking/relevance score.
            reason: Explanation for the recommendation.
            agent_source: Agent that generated the recommendation.

        Returns:
            The persisted Recommendation record.

        Raises:
            RecommendationRepositoryError: On unexpected database errors.
        """
        try:
            record = Recommendation(
                user_id=str(user_id),
                session_id=str(session_id),
                product_id=str(product_id),
                product_name=product_name,
                score=score,
                reason=reason,
                agent_source=agent_source,
            )

            self._db.add(record)
            await self._db.commit()
            await self._db.refresh(record)

            logger.info(
                "Saved recommendation id=%s for user=%s product=%s",
                record.id,
                user_id,
                product_name,
            )
            return record

        except SQLAlchemyError as exc:
            await self._db.rollback()
            logger.error(
                "Failed to save recommendation for user=%s: %s", user_id, exc
            )
            raise RecommendationRepositoryError(
                f"Failed to save recommendation: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Retrieve
    # ------------------------------------------------------------------

    async def get_recommendations(
        self,
        user_id: UUID | str,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Recommendation]:
        """Get recent recommendations for a user.

        Args:
            user_id: UUID of the user.
            limit: Maximum results to return.
            offset: Pagination offset.

        Returns:
            List of Recommendation records, most recent first.

        Raises:
            RecommendationRepositoryError: On unexpected database errors.
        """
        try:
            stmt = (
                select(Recommendation)
                .where(Recommendation.user_id == str(user_id))
                .order_by(desc(Recommendation.created_at))
            )

            stmt = stmt.limit(limit).offset(offset)
            result = await self._db.execute(stmt)
            records = list(result.scalars().all())

            logger.debug(
                "Retrieved %d recommendations for user=%s", len(records), user_id
            )
            return records

        except SQLAlchemyError as exc:
            logger.error(
                "Failed to get recommendations for user=%s: %s", user_id, exc
            )
            raise RecommendationRepositoryError(
                f"Failed to retrieve recommendations: {exc}"
            ) from exc

    async def get_history(
        self,
        user_id: UUID,
        *,
        days: int | None = None,
        limit: int = 50,
    ) -> list[Recommendation]:
        """Get recommendation history for a user with optional time window.

        Args:
            user_id: UUID of the user.
            days: If set, only return recommendations from the last N days.
            limit: Maximum results.

        Returns:
            List of Recommendation records ordered by creation date.

        Raises:
            RecommendationRepositoryError: On unexpected database errors.
        """
        try:
            stmt = (
                select(Recommendation)
                .where(Recommendation.user_id == user_id)
                .order_by(desc(Recommendation.created_at))
            )

            if days is not None:
                from datetime import timedelta

                cutoff = datetime.now(timezone.utc) - timedelta(days=days)
                stmt = stmt.where(Recommendation.created_at >= cutoff)

            stmt = stmt.limit(limit)
            result = await self._db.execute(stmt)
            records = list(result.scalars().all())

            logger.debug(
                "Retrieved %d history records for user id=%s (days=%s)",
                len(records),
                user_id,
                days,
            )
            return records

        except SQLAlchemyError as exc:
            logger.error(
                "Failed to get recommendation history for user id=%s: %s",
                user_id,
                exc,
            )
            raise RecommendationRepositoryError(
                f"Failed to retrieve recommendation history: {exc}"
            ) from exc

    async def get_by_id(self, recommendation_id: UUID) -> Recommendation | None:
        """Retrieve a single recommendation by ID.

        Args:
            recommendation_id: UUID of the recommendation record.

        Returns:
            Recommendation record or None if not found.

        Raises:
            RecommendationRepositoryError: On unexpected database errors.
        """
        try:
            stmt = select(Recommendation).where(Recommendation.id == recommendation_id)
            result = await self._db.execute(stmt)
            record = result.scalar_one_or_none()

            if record:
                logger.debug("Found recommendation id=%s", recommendation_id)
            else:
                logger.debug("Recommendation id=%s not found", recommendation_id)

            return record

        except SQLAlchemyError as exc:
            logger.error(
                "Failed to get recommendation id=%s: %s", recommendation_id, exc
            )
            raise RecommendationRepositoryError(
                f"Failed to retrieve recommendation: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    async def delete_recommendation(self, recommendation_id: UUID) -> bool:
        """Delete a specific recommendation record.

        Args:
            recommendation_id: UUID of the recommendation to delete.

        Returns:
            True if deleted, False if not found.

        Raises:
            RecommendationRepositoryError: On unexpected database errors.
        """
        try:
            record = await self.get_by_id(recommendation_id)
            if record is None:
                logger.debug(
                    "Recommendation id=%s not found for deletion", recommendation_id
                )
                return False

            await self._db.delete(record)
            await self._db.commit()

            logger.info("Deleted recommendation id=%s", recommendation_id)
            return True

        except RecommendationRepositoryError:
            raise
        except SQLAlchemyError as exc:
            await self._db.rollback()
            logger.error(
                "Failed to delete recommendation id=%s: %s", recommendation_id, exc
            )
            raise RecommendationRepositoryError(
                f"Failed to delete recommendation: {exc}"
            ) from exc

    async def delete_user_recommendations(self, user_id: UUID) -> int:
        """Delete all recommendations for a user.

        Args:
            user_id: UUID of the user.

        Returns:
            Number of records deleted.

        Raises:
            RecommendationRepositoryError: On unexpected database errors.
        """
        try:
            records = await self.get_recommendations(user_id, limit=10000)
            count = len(records)

            for record in records:
                await self._db.delete(record)

            await self._db.commit()

            logger.info(
                "Deleted %d recommendations for user id=%s", count, user_id
            )
            return count

        except RecommendationRepositoryError:
            raise
        except SQLAlchemyError as exc:
            await self._db.rollback()
            logger.error(
                "Failed to delete recommendations for user id=%s: %s", user_id, exc
            )
            raise RecommendationRepositoryError(
                f"Failed to delete user recommendations: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Analytics
    # ------------------------------------------------------------------

    async def get_analytics(
        self,
        user_id: UUID | str | None = None,
    ) -> RecommendationAnalytics:
        """Generate analytics for recommendation usage.

        Args:
            user_id: If provided, scope analytics to a single user.

        Returns:
            RecommendationAnalytics object with aggregated metrics.
        """
        try:
            from datetime import timedelta

            now = datetime.now(timezone.utc)

            base_filter = (
                Recommendation.user_id == str(user_id) if user_id else True
            )

            # Total count
            stmt_count = select(func.count()).select_from(Recommendation).where(base_filter)
            total = (await self._db.execute(stmt_count)).scalar_one()

            # Average score
            stmt_avg = select(func.avg(Recommendation.score)).where(base_filter)
            avg_score = (await self._db.execute(stmt_avg)).scalar_one() or 0.0

            # Recent count (7 days)
            cutoff_7d = now - timedelta(days=7)
            stmt_7d = (
                select(func.count())
                .select_from(Recommendation)
                .where(base_filter)
                .where(Recommendation.created_at >= cutoff_7d)
            )
            recent_7d = (await self._db.execute(stmt_7d)).scalar_one()

            # Recent count (30 days)
            cutoff_30d = now - timedelta(days=30)
            stmt_30d = (
                select(func.count())
                .select_from(Recommendation)
                .where(base_filter)
                .where(Recommendation.created_at >= cutoff_30d)
            )
            recent_30d = (await self._db.execute(stmt_30d)).scalar_one()

            # Top agent sources
            stmt_agents = (
                select(Recommendation.agent_source, func.count().label("count"))
                .where(base_filter)
                .group_by(Recommendation.agent_source)
                .order_by(desc("count"))
                .limit(10)
            )
            agent_result = await self._db.execute(stmt_agents)
            top_categories = [
                {"category": row[0], "count": row[1]}
                for row in agent_result.all()
            ]

            analytics = RecommendationAnalytics(
                total_recommendations=total,
                avg_confidence=float(avg_score),
                top_categories=top_categories,
                recent_count_7d=recent_7d,
                recent_count_30d=recent_30d,
            )

            logger.info(
                "Generated analytics (user=%s): total=%d",
                user_id or "system",
                total,
            )
            return analytics

        except SQLAlchemyError as exc:
            logger.error("Failed to generate analytics: %s", exc)
            raise RecommendationRepositoryError(
                f"Failed to generate analytics: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    async def count(self, user_id: UUID | None = None) -> int:
        """Return the total number of recommendation records.

        Args:
            user_id: If provided, count only for this user.
        """
        try:
            stmt = select(func.count()).select_from(Recommendation)
            if user_id:
                stmt = stmt.where(Recommendation.user_id == user_id)
            result = await self._db.execute(stmt)
            return result.scalar_one()
        except SQLAlchemyError as exc:
            logger.error("Failed to count recommendations: %s", exc)
            raise RecommendationRepositoryError(
                "Failed to count recommendations"
            ) from exc

    async def save(self) -> None:
        """Flush and commit the current session."""
        try:
            await self._db.commit()
        except SQLAlchemyError as exc:
            await self._db.rollback()
            logger.error("Failed to save session: %s", exc)
            raise RecommendationRepositoryError("Failed to save session") from exc
