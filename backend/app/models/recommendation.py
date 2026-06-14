"""Recommendation model for NeedNow AI.

Stores generated product recommendations linked to users, sessions,
and the agent source that produced them.
"""

import uuid

from sqlalchemy import DateTime, Float, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[str] = mapped_column(
        String(255),
        index=True,
        nullable=False,
    )

    session_id: Mapped[str] = mapped_column(
        String(255),
        index=True,
        nullable=False,
    )

    product_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    product_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    agent_source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        return (
            f"<Recommendation(id={self.id!r}, user_id={self.user_id!r}, "
            f"product_name={self.product_name!r}, score={self.score}, "
            f"agent_source={self.agent_source!r})>"
        )
