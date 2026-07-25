"""Async database engine and session management."""

from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from earthdata.core.config import Settings


@lru_cache
def get_engine(settings: Settings) -> AsyncEngine:
    """Return a process-wide cached async SQLAlchemy engine.

    Cached per `Settings` instance so tests can override the database URL
    (e.g. to a SQLite/Postgres test database) and receive a distinct engine.
    """
    return create_async_engine(
        settings.database_url,
        echo=settings.database_echo,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_pre_ping=True,
    )


@lru_cache
def get_session_factory(settings: Settings) -> async_sessionmaker[AsyncSession]:
    """Return a process-wide cached session factory bound to the engine."""
    engine = get_engine(settings)
    return async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
