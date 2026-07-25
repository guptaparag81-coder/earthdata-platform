"""Tests for `AnalyticsService`."""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from earthdata.analytics.schemas import TimeSeriesInterval
from earthdata.analytics.service import AnalyticsService
from earthdata.db.models.processed_observation import ProcessedObservation
from earthdata.db.models.raw_observation import RawObservation
from earthdata.repositories.processed_observation_repository import (
    ProcessedObservationRepository,
)
from earthdata.repositories.raw_observation_repository import RawObservationRepository


async def _seed(session: AsyncSession) -> AnalyticsService:
    raw_repository = RawObservationRepository(session)
    processed_repository = ProcessedObservationRepository(session)
    now = datetime.now(UTC)

    fixtures = [
        ("W1", "Wildfires", "eonet", True, now - timedelta(days=1)),
        ("W2", "Wildfires", "eonet", False, now),
        ("S1", "Severe Storms", "other", True, now),
    ]
    for external_id, category, source, is_open, event_date in fixtures:
        raw = await raw_repository.add(
            RawObservation(
                source=source,
                external_id=external_id,
                payload={"id": external_id},
                fetched_at=now,
            )
        )
        await processed_repository.upsert(
            ProcessedObservation(
                raw_observation_id=raw.id,
                external_id=external_id,
                title=f"Event {external_id}",
                category=category,
                source=source,
                event_date=event_date,
                latitude=1.0,
                longitude=2.0,
                is_open=is_open,
            )
        )
    return AnalyticsService(processed_repository)


async def test_get_summary(db_session: AsyncSession) -> None:
    service = await _seed(db_session)

    summary = await service.get_summary()

    assert summary.total_count == 3
    assert summary.open_count == 2
    assert summary.closed_count == 1
    assert {row.category for row in summary.by_category} == {"Wildfires", "Severe Storms"}
    assert {row.source for row in summary.by_source} == {"eonet", "other"}
    assert summary.earliest_event_date is not None
    assert summary.latest_event_date is not None


async def test_get_summary_on_empty_dataset(db_session: AsyncSession) -> None:
    service = AnalyticsService(ProcessedObservationRepository(db_session))

    summary = await service.get_summary()

    assert summary.total_count == 0
    assert summary.open_count == 0
    assert summary.closed_count == 0
    assert summary.by_category == []
    assert summary.by_source == []
    assert summary.earliest_event_date is None
    assert summary.latest_event_date is None


async def test_get_timeseries(db_session: AsyncSession) -> None:
    service = await _seed(db_session)

    result = await service.get_timeseries(interval=TimeSeriesInterval.DAY)

    assert result.interval == TimeSeriesInterval.DAY
    assert sum(point.count for point in result.points) == 3


async def test_get_timeseries_filtered_by_category(db_session: AsyncSession) -> None:
    service = await _seed(db_session)

    result = await service.get_timeseries(interval=TimeSeriesInterval.DAY, category="Wildfires")

    assert sum(point.count for point in result.points) == 2


async def test_export_rows(db_session: AsyncSession) -> None:
    service = await _seed(db_session)

    rows = await service.export_rows(category="Wildfires")

    assert {row.external_id for row in rows} == {"W1", "W2"}
    assert all(isinstance(row.id, uuid.UUID) for row in rows)
