import uuid

from sqlalchemy import (
    String,
    Text,
    Float,
    Integer,
    DateTime,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, mapped_column, Mapped

from app.database.base import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    title: Mapped[str] = mapped_column(
        String(500),
        index=True,
    )

    description: Mapped[str] = mapped_column(
        Text,
    )

    category: Mapped[str] = mapped_column(
        String(255),
        index=True,
    )

    brand: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    price: Mapped[float] = mapped_column(Float)

    stock: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    image_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    cart_items = relationship(
        "CartItem",
        back_populates="product",
    )

    embedding = relationship(
        "ProductEmbedding",
        back_populates="product",
        uselist=False,
        cascade="all, delete-orphan",
    )