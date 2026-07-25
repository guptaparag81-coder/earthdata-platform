"""Repository for `RawObservation` records."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from sqlalchemy import func, select
from sqlalchemy.sql import Select

from earthdata.db.models.processed_observation import ProcessedObservation
from earthdata.db.models.raw_observation import RawObservation
from earthdata.repositories.base import BaseRepository

RawSortField = Literal["created_at", "fetched_at", "source", "external_id"]

_SORT_COLUMNS: dict[str, Any] = {
    "created_at": RawObservation.created_at,
    "fetched_at": RawObservation.fetched_at,
    "source": RawObservation.source,
    "external_id": RawObservation.external_id,
}


class RawObservationRepository(BaseRepository[RawObservation]):
    """Persistence operations for raw ingested observation payloads."""

    model = RawObservation

    def _filtered_query(
        self,
        *,
        source: str | None,
        external_id: str | None,
        fetched_after: datetime | None,
        fetched_before: datetime | None,
    ) -> Select[tuple[RawObservation]]:
        stmt = select(RawObservation)
        if source is not None:
            stmt = stmt.where(RawObservation.source == source)
        if external_id is not None:
            stmt = stmt.where(RawObservation.external_id == external_id)
        if fetched_after is not None:
            stmt = stmt.where(RawObservation.fetched_at >= fetched_after)
        if fetched_before is not None:
            stmt = stmt.where(RawObservation.fetched_at <= fetched_before)
        return stmt

    async def list_filtered(
        self,
        *,
        limit: int,
        offset: int,
        source: str | None = None,
        external_id: str | None = None,
        fetched_after: datetime | None = None,
        fetched_before: datetime | None = None,
        sort_by: RawSortField = "created_at",
        sort_order: Literal["asc", "desc"] = "desc",
    ) -> list[RawObservation]:
        """List raw observations matching the given filters, paginated and sorted."""
        stmt = self._filtered_query(
            source=source,
            external_id=external_id,
            fetched_after=fetched_after,
            fetched_before=fetched_before,
        )
        column = _SORT_COLUMNS[sort_by]
        stmt = stmt.order_by(column.desc() if sort_order == "desc" else column.asc())
        stmt = stmt.limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_filtered(
        self,
        *,
        source: str | None = None,
        external_id: str | None = None,
        fetched_after: datetime | None = None,
        fetched_before: datetime | None = None,
    ) -> int:
        """Count raw observations matching the given filters."""
        stmt = self._filtered_query(
            source=source,
            external_id=external_id,
            fetched_after=fetched_after,
            fetched_before=fetched_before,
        )
        count_stmt = select(func.count()).select_from(stmt.subquery())
        result = await self._session.execute(count_stmt)
        return int(result.scalar_one())

    async def get_by_source_and_external_id(
        self, source: str, external_id: str
    ) -> RawObservation | None:
        """Fetch the raw record for a given source/external id pair, if any."""
        stmt = select(RawObservation).where(
            RawObservation.source == source,
            RawObservation.external_id == external_id,
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def list_unprocessed(self, *, limit: int = 100) -> list[RawObservation]:
        """List raw observations that do not yet have a processed counterpart."""
        stmt = (
            select(RawObservation)
            .outerjoin(
                ProcessedObservation,
                ProcessedObservation.raw_observation_id == RawObservation.id,
            )
            .where(ProcessedObservation.id.is_(None))
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
