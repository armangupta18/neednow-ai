import uuid

from sqlalchemy import (
    String,
    Text,
    ForeignKey,
    DateTime,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, mapped_column, Mapped

from app.database.base import Base


class Situation(Base):
    __tablename__ = "situations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        index=True,
    )

    raw_input: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    detected_intent: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    urgency_score: Mapped[float | None] = mapped_column(
        nullable=True,
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    user = relationship(
        "User",
        back_populates="situations",
    )

    session = relationship(
        "Session",
        back_populates="situations",
    )

    cart = relationship(
        "Cart",
        back_populates="situation",
        uselist=False,
        cascade="all, delete-orphan",
    )