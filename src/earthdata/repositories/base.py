"""Generic async repository base class."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from earthdata.db.base import Base


class BaseRepository[ModelT: Base]:
    """Common async CRUD operations shared by all repositories.

    Concrete repositories declare the ORM model they operate on and may add
    domain-specific query methods on top of this base.
    """

    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, record_id: uuid.UUID) -> ModelT | None:
        """Fetch a single record by primary key, or `None` if not found."""
        return await self._session.get(self.model, record_id)

    async def list_all(self, *, limit: int = 100, offset: int = 0) -> list[ModelT]:
        """List records with pagination."""
        stmt = select(self.model).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def add(self, instance: ModelT) -> ModelT:
        """Persist a single new record and flush it to the database."""
        self._session.add(instance)
        await self._session.flush()
        return instance

    async def bulk_add(self, instances: list[ModelT]) -> list[ModelT]:
        """Persist multiple new records in one flush."""
        self._session.add_all(instances)
        await self._session.flush()
        return instances

    async def update(self, instance: ModelT) -> ModelT:
        """Flush pending in-place attribute changes on a tracked instance.

        Columns with a server-evaluated `onupdate` (e.g. `updated_at`) are
        expired by the flush and must be refreshed here, inside the async
        context, so callers can safely read every attribute afterward.
        """
        await self._session.flush()
        await self._session.refresh(instance)
        return instance

    async def delete(self, instance: ModelT) -> None:
        """Delete a single record and flush the deletion."""
        await self._session.delete(instance)
        await self._session.flush()
