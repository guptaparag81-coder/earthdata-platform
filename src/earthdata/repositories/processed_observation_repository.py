"""Repository for `ProcessedObservation` records."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import Any, Literal

from sqlalchemy import Row, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.sql import Select

from earthdata.db.models.processed_observation import ProcessedObservation
from earthdata.repositories.base import BaseRepository

ProcessedSortField = Literal[
    "created_at", "updated_at", "event_date", "title", "category", "source", "external_id"
]
TimeSeriesInterval = Literal["day", "week", "month"]

_SORT_COLUMNS: dict[str, Any] = {
    "created_at": ProcessedObservation.created_at,
    "updated_at": ProcessedObservation.updated_at,
    "event_date": ProcessedObservation.event_date,
    "title": ProcessedObservation.title,
    "category": ProcessedObservation.category,
    "source": ProcessedObservation.source,
    "external_id": ProcessedObservation.external_id,
}


class ProcessedObservationRepository(BaseRepository[ProcessedObservation]):
    """Persistence operations for cleaned/transformed observation records."""

    model = ProcessedObservation

    async def get_by_external_id(self, external_id: str) -> ProcessedObservation | None:
        """Fetch a processed record by its upstream external id, if any."""
        stmt = select(ProcessedObservation).where(ProcessedObservation.external_id == external_id)
        result = await self._session.execute(stmt)
        return result.scalars().first()

    def _filtered_query(
        self,
        *,
        category: str | None,
        source: str | None,
        is_open: bool | None,
        external_id: str | None,
        event_after: datetime | None,
        event_before: datetime | None,
    ) -> Select[tuple[ProcessedObservation]]:
        stmt = select(ProcessedObservation)
        if category is not None:
            stmt = stmt.where(ProcessedObservation.category == category)
        if source is not None:
            stmt = stmt.where(ProcessedObservation.source == source)
        if is_open is not None:
            stmt = stmt.where(ProcessedObservation.is_open == is_open)
        if external_id is not None:
            stmt = stmt.where(ProcessedObservation.external_id == external_id)
        if event_after is not None:
            stmt = stmt.where(ProcessedObservation.event_date >= event_after)
        if event_before is not None:
            stmt = stmt.where(ProcessedObservation.event_date <= event_before)
        return stmt

    async def list_filtered(
        self,
        *,
        limit: int,
        offset: int,
        category: str | None = None,
        source: str | None = None,
        is_open: bool | None = None,
        external_id: str | None = None,
        event_after: datetime | None = None,
        event_before: datetime | None = None,
        sort_by: ProcessedSortField = "event_date",
        sort_order: Literal["asc", "desc"] = "desc",
    ) -> list[ProcessedObservation]:
        """List processed observations matching the given filters, paginated and sorted."""
        stmt = self._filtered_query(
            category=category,
            source=source,
            is_open=is_open,
            external_id=external_id,
            event_after=event_after,
            event_before=event_before,
        )
        column = _SORT_COLUMNS[sort_by]
        stmt = stmt.order_by(column.desc() if sort_order == "desc" else column.asc())
        stmt = stmt.limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_filtered(
        self,
        *,
        category: str | None = None,
        source: str | None = None,
        is_open: bool | None = None,
        external_id: str | None = None,
        event_after: datetime | None = None,
        event_before: datetime | None = None,
    ) -> int:
        """Count processed observations matching the given filters."""
        stmt = self._filtered_query(
            category=category,
            source=source,
            is_open=is_open,
            external_id=external_id,
            event_after=event_after,
            event_before=event_before,
        )
        count_stmt = select(func.count()).select_from(stmt.subquery())
        result = await self._session.execute(count_stmt)
        return int(result.scalar_one())

    async def count_total(self) -> int:
        """Count all processed observations."""
        result = await self._session.execute(select(func.count()).select_from(ProcessedObservation))
        return int(result.scalar_one())

    async def count_open(self) -> int:
        """Count processed observations whose upstream event is still open."""
        stmt = (
            select(func.count())
            .select_from(ProcessedObservation)
            .where(ProcessedObservation.is_open.is_(True))
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def count_by_category(self) -> Sequence[Row[tuple[str, int]]]:
        """Count processed observations grouped by category."""
        stmt = (
            select(ProcessedObservation.category, func.count())
            .group_by(ProcessedObservation.category)
            .order_by(func.count().desc())
        )
        result = await self._session.execute(stmt)
        return result.all()

    async def count_by_source(self) -> Sequence[Row[tuple[str, int]]]:
        """Count processed observations grouped by source."""
        stmt = (
            select(ProcessedObservation.source, func.count())
            .group_by(ProcessedObservation.source)
            .order_by(func.count().desc())
        )
        result = await self._session.execute(stmt)
        return result.all()

    async def get_event_date_bounds(self) -> tuple[datetime | None, datetime | None]:
        """Return the earliest and latest `event_date` across all records."""
        stmt = select(
            func.min(ProcessedObservation.event_date), func.max(ProcessedObservation.event_date)
        )
        result = await self._session.execute(stmt)
        earliest, latest = result.one()
        return earliest, latest

    async def get_timeseries(
        self,
        *,
        interval: TimeSeriesInterval,
        start: datetime | None = None,
        end: datetime | None = None,
        category: str | None = None,
        source: str | None = None,
    ) -> Sequence[Row[tuple[datetime, int]]]:
        """Count processed observations bucketed into time intervals.

        Buckets are computed with PostgreSQL's `date_trunc`, grouping event
        dates into the given interval (day/week/month).
        """
        bucket = func.date_trunc(interval, ProcessedObservation.event_date).label("bucket")
        stmt = select(bucket, func.count()).group_by(bucket).order_by(bucket)

        if start is not None:
            stmt = stmt.where(ProcessedObservation.event_date >= start)
        if end is not None:
            stmt = stmt.where(ProcessedObservation.event_date <= end)
        if category is not None:
            stmt = stmt.where(ProcessedObservation.category == category)
        if source is not None:
            stmt = stmt.where(ProcessedObservation.source == source)

        result = await self._session.execute(stmt)
        return result.all()

    async def upsert(self, instance: ProcessedObservation) -> ProcessedObservation:
        """Insert a processed record, or update it in place if it already exists.

        Uses a PostgreSQL `ON CONFLICT` upsert keyed on `external_id` so that
        reprocessing the same upstream event is idempotent. `instance.id` is
        normally unset (it is an ORM-side default only applied on flush), so a
        new id is generated here for the insert branch; the conflict branch
        never touches `id`, so an existing row keeps its original identity.
        """
        stmt = (
            pg_insert(ProcessedObservation)
            .values(
                id=instance.id or uuid.uuid4(),
                raw_observation_id=instance.raw_observation_id,
                external_id=instance.external_id,
                title=instance.title,
                category=instance.category,
                source=instance.source,
                event_date=instance.event_date,
                latitude=instance.latitude,
                longitude=instance.longitude,
                is_open=instance.is_open,
            )
            .on_conflict_do_update(
                index_elements=[ProcessedObservation.external_id],
                set_={
                    "title": instance.title,
                    "category": instance.category,
                    "event_date": instance.event_date,
                    "latitude": instance.latitude,
                    "longitude": instance.longitude,
                    "is_open": instance.is_open,
                    "raw_observation_id": instance.raw_observation_id,
                },
            )
            .returning(ProcessedObservation.id)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        upserted_id = result.scalar_one()

        # Re-fetch by id with `populate_existing` rather than trusting a
        # `.returning(ProcessedObservation)` ORM row: if this session already
        # has the conflicting row's identity loaded (e.g. from an earlier
        # `get_by_external_id` call), the ORM DML-returning path can hand back
        # that stale, pre-update object instead of the freshly written one.
        upserted = await self._session.get(
            ProcessedObservation, upserted_id, populate_existing=True
        )
        assert upserted is not None  # guaranteed by the insert/update above
        return upserted
