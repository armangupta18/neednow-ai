"""Async database connection for NeedNow AI.

Provides SQLAlchemy 2.0 async engine, session factory, dependency
injection helper, and table initialization utility.

Compatible with Neon PostgreSQL (handles sslmode and channel_binding
query params that asyncpg doesn't support natively).
"""

from __future__ import annotations

import ssl
from collections.abc import AsyncGenerator
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.database.base import Base

# ---------------------------------------------------------------------------
# URL Processing for Neon + asyncpg compatibility
# ---------------------------------------------------------------------------

# Parameters that are libpq-specific and not understood by asyncpg
_STRIP_PARAMS = {"sslmode", "channel_binding", "options"}


def _prepare_async_url(raw_url: str) -> tuple[str, dict]:
    """Convert a Neon PostgreSQL URL to asyncpg-compatible format.

    - Swaps the driver to postgresql+asyncpg://
    - Strips libpq-only query params (sslmode, channel_binding)
    - Returns connect_args with SSL context if sslmode was present

    Returns:
        Tuple of (cleaned_url, connect_args_dict)
    """
    # Swap driver prefix
    url = raw_url
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)

    # Parse and strip incompatible query params
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)

    # Detect if SSL is required
    ssl_required = query_params.get("sslmode", [None])[0] in (
        "require",
        "verify-ca",
        "verify-full",
    )

    # Remove incompatible params
    cleaned_params = {
        k: v[0] if len(v) == 1 else v
        for k, v in query_params.items()
        if k not in _STRIP_PARAMS
    }

    # Rebuild URL without stripped params
    cleaned_query = urlencode(cleaned_params, doseq=True)
    cleaned_url = urlunparse(parsed._replace(query=cleaned_query))

    # Build connect_args for asyncpg
    connect_args: dict = {}
    if ssl_required:
        # Create an SSL context that doesn't verify certificates
        # (Neon uses valid certs, but this avoids CA bundle issues)
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
        connect_args["ssl"] = ssl_ctx

    return cleaned_url, connect_args


# ---------------------------------------------------------------------------
# Engine & Session Factory
# ---------------------------------------------------------------------------

_database_url, _connect_args = _prepare_async_url(settings.DATABASE_URL)

engine = create_async_engine(
    _database_url,
    echo=False,
    future=True,
    connect_args=_connect_args,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ---------------------------------------------------------------------------
# Dependency Injection
# ---------------------------------------------------------------------------


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session.

    Usage:
        @router.get("/")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        yield session


# ---------------------------------------------------------------------------
# Table Initialization
# ---------------------------------------------------------------------------


async def init_db() -> None:
    """Create all database tables from registered SQLAlchemy models.

    Imports all models to ensure they are registered with Base.metadata
    before issuing CREATE TABLE statements.
    """
    # Import all models so they register with Base.metadata
    import app.models.user  # noqa: F401
    import app.models.session  # noqa: F401
    import app.models.situation  # noqa: F401
    import app.models.cart  # noqa: F401
    import app.models.cart_item  # noqa: F401
    import app.models.product  # noqa: F401
    import app.models.product_embedding  # noqa: F401
    import app.models.feedback  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
