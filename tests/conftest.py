"""Shared pytest fixtures.

Real-database fixtures (`db_settings`, `db_session`, `db_client`) spin up an
ephemeral PostgreSQL database per test via `pytest-postgresql` (using the
locally installed `postgres`/`initdb` binaries, no Docker required) so that
repository, service, and API tests exercise real SQL (JSONB, UUID, upserts)
rather than mocks.
"""

from collections.abc import AsyncIterator
from typing import Any

import psycopg
import pytest
from httpx import ASGITransport, AsyncClient
from pytest_postgresql import factories
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from earthdata.core.config import Settings, get_settings
from earthdata.core.di import get_db_session
from earthdata.db.base import Base
from earthdata.db.session import get_engine, get_session_factory
from earthdata.main import create_app

postgresql_proc = factories.postgresql_proc(port=None)
postgresql = factories.postgresql("postgresql_proc")


@pytest.fixture
def settings() -> Settings:
    return Settings(app_env="test", database_url="postgresql+asyncpg://test:test@localhost/test")


class _FakeResult:
    def __init__(self, value: int = 1) -> None:
        self._value = value

    def scalar_one(self) -> int:
        return self._value


class _FakeSession:
    """Minimal async session stand-in used to avoid a real DB in API tests."""

    async def execute(self, *_args: object, **_kwargs: object) -> _FakeResult:
        return _FakeResult()


class _FailingSession:
    """Async session stand-in that simulates a database outage."""

    async def execute(self, *_args: object, **_kwargs: object) -> _FakeResult:
        raise ConnectionError("database unavailable")


@pytest.fixture
async def client(settings: Settings) -> AsyncIterator[AsyncClient]:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: settings

    async def _fake_db_session() -> AsyncIterator[_FakeSession]:
        yield _FakeSession()

    app.dependency_overrides[get_db_session] = _fake_db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client


@pytest.fixture
async def failing_client(settings: Settings) -> AsyncIterator[AsyncClient]:
    """A client wired to a session whose `execute` always raises."""
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: settings

    async def _failing_db_session() -> AsyncIterator[_FailingSession]:
        yield _FailingSession()

    app.dependency_overrides[get_db_session] = _failing_db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client


@pytest.fixture
def db_settings(postgresql: psycopg.Connection[Any]) -> Settings:
    """Settings pointing at a freshly created, empty ephemeral test database."""
    info = postgresql.info
    url = f"postgresql+asyncpg://{info.user}:@{info.host}:{info.port}/{info.dbname}"
    return Settings(app_env="test", database_url=url)


@pytest.fixture
async def db_session(db_settings: Settings) -> AsyncIterator[AsyncSession]:
    """A real `AsyncSession` bound to an ephemeral PostgreSQL database with schema applied.

    `pytest-postgresql` drops and recreates the same physical database
    (typically named "tests") for every test rather than minting a unique
    name each time. `get_engine`/`get_session_factory` are process-wide
    `lru_cache`d by `Settings`, so an identical `database_url` across tests
    would otherwise hand back a pool holding connections to a database that
    has since been dropped out from under it. Clearing both caches on
    teardown forces a fresh engine (and pool) per test.
    """
    engine = get_engine(db_settings)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    try:
        async with session_factory() as session:
            yield session
    finally:
        await engine.dispose()
        get_engine.cache_clear()
        get_session_factory.cache_clear()


@pytest.fixture
async def db_client(db_settings: Settings) -> AsyncIterator[AsyncClient]:
    """An HTTP client wired to the real FastAPI app and an ephemeral PostgreSQL database.

    See `db_session` for why the engine/session-factory caches must be
    cleared on teardown when reusing the same physical test database.
    """
    engine = get_engine(db_settings)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    app = create_app()
    app.dependency_overrides[get_settings] = lambda: db_settings

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
            yield async_client
    finally:
        await engine.dispose()
        get_engine.cache_clear()
        get_session_factory.cache_clear()
