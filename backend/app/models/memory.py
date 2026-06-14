"""Memory model for NeedNow AI.

Stores user memory entries (preferences, purchases, behavior) with
optional embedding references for semantic retrieval.
"""

import uuid

from sqlalchemy import DateTime, Float, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Memory(Base):
    __tablename__ = "memories"

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

    memory_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    embedding_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    importance_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return (
            f"<Memory(id={self.id!r}, user_id={self.user_id!r}, "
            f"memory_type={self.memory_type!r}, importance={self.importance_score})>"
        )
