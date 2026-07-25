"""Tests for `ProcessedObservationRepository` query and aggregation methods."""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from earthdata.db.models.processed_observation import ProcessedObservation
from earthdata.db.models.raw_observation import RawObservation
from earthdata.repositories.processed_observation_repository import (
    ProcessedObservationRepository,
)
from earthdata.repositories.raw_observation_repository import RawObservationRepository


async def _make_raw_id(session: AsyncSession, external_id: str) -> uuid.UUID:
    raw_repository = RawObservationRepository(session)
    raw = await raw_repository.add(
        RawObservation(
            source="eonet",
            external_id=external_id,
            payload={"id": external_id},
            fetched_at=datetime.now(UTC),
        )
    )
    return raw.id


async def _seed(session: AsyncSession) -> ProcessedObservationRepository:
    repository = ProcessedObservationRepository(session)
    now = datetime.now(UTC)

    fixtures = [
        ("W1", "Wildfires", "eonet", True, now - timedelta(days=2), 10.0, 20.0),
        ("W2", "Wildfires", "eonet", False, now - timedelta(days=1), 11.0, 21.0),
        ("S1", "Severe Storms", "other", True, now, 12.0, 22.0),
    ]
    for external_id, category, source, is_open, event_date, lat, lon in fixtures:
        raw_id = await _make_raw_id(session, external_id)
        await repository.upsert(
            ProcessedObservation(
                raw_observation_id=raw_id,
                external_id=external_id,
                title=f"Event {external_id}",
                category=category,
                source=source,
                event_date=event_date,
                latitude=lat,
                longitude=lon,
                is_open=is_open,
            )
        )
    return repository


async def test_get_by_external_id_found_and_missing(db_session: AsyncSession) -> None:
    repository = await _seed(db_session)

    found = await repository.get_by_external_id("W1")
    assert found is not None
    assert found.category == "Wildfires"

    assert await repository.get_by_external_id("missing") is None


async def test_upsert_updates_existing_record(db_session: AsyncSession) -> None:
    repository = await _seed(db_session)
    existing = await repository.get_by_external_id("W1")
    assert existing is not None

    updated = await repository.upsert(
        ProcessedObservation(
            raw_observation_id=existing.raw_observation_id,
            external_id="W1",
            title="Updated title",
            category="Wildfires",
            source="eonet",
            event_date=existing.event_date,
            latitude=existing.latitude,
            longitude=existing.longitude,
            is_open=False,
        )
    )

    assert updated.id == existing.id
    assert updated.title == "Updated title"
    assert updated.is_open is False

    total = await repository.count_total()
    assert total == 3


async def test_list_filtered_by_category_and_open(db_session: AsyncSession) -> None:
    repository = await _seed(db_session)

    wildfires = await repository.list_filtered(limit=10, offset=0, category="Wildfires")
    assert {r.external_id for r in wildfires} == {"W1", "W2"}

    open_only = await repository.list_filtered(limit=10, offset=0, is_open=True)
    assert {r.external_id for r in open_only} == {"W1", "S1"}


async def test_list_filtered_by_event_date_range(db_session: AsyncSession) -> None:
    repository = await _seed(db_session)
    now = datetime.now(UTC)

    results = await repository.list_filtered(
        limit=10,
        offset=0,
        event_after=now - timedelta(days=1, hours=1),
        event_before=now - timedelta(hours=1),
    )
    assert [r.external_id for r in results] == ["W2"]


async def test_list_filtered_sort_and_pagination(db_session: AsyncSession) -> None:
    repository = await _seed(db_session)

    ascending = await repository.list_filtered(
        limit=2, offset=0, sort_by="event_date", sort_order="asc"
    )
    assert [r.external_id for r in ascending] == ["W1", "W2"]

    remaining = await repository.list_filtered(
        limit=2, offset=2, sort_by="event_date", sort_order="asc"
    )
    assert [r.external_id for r in remaining] == ["S1"]


async def test_count_filtered(db_session: AsyncSession) -> None:
    repository = await _seed(db_session)

    assert await repository.count_filtered() == 3
    assert await repository.count_filtered(source="other") == 1
    assert await repository.count_filtered(external_id="W1") == 1


async def test_count_total_and_open(db_session: AsyncSession) -> None:
    repository = await _seed(db_session)

    assert await repository.count_total() == 3
    assert await repository.count_open() == 2


async def test_count_by_category_and_source(db_session: AsyncSession) -> None:
    repository = await _seed(db_session)

    # dict comprehension (not dict()) needed: mypy can't resolve Row's tuple
    # element types through the dict() constructor overload.
    by_category = {  # noqa: C416
        category: count for category, count in await repository.count_by_category()
    }
    assert by_category == {"Wildfires": 2, "Severe Storms": 1}

    by_source = {  # noqa: C416
        source: count for source, count in await repository.count_by_source()
    }
    assert by_source == {"eonet": 2, "other": 1}


async def test_get_event_date_bounds(db_session: AsyncSession) -> None:
    repository = await _seed(db_session)

    earliest, latest = await repository.get_event_date_bounds()
    assert earliest is not None
    assert latest is not None
    assert earliest <= latest


async def test_get_event_date_bounds_empty_table(db_session: AsyncSession) -> None:
    repository = ProcessedObservationRepository(db_session)

    earliest, latest = await repository.get_event_date_bounds()
    assert earliest is None
    assert latest is None


async def test_get_timeseries_buckets_by_day(db_session: AsyncSession) -> None:
    repository = await _seed(db_session)

    rows = await repository.get_timeseries(interval="day")
    assert sum(count for _, count in rows) == 3


async def test_get_timeseries_filters_by_category_and_range(db_session: AsyncSession) -> None:
    repository = await _seed(db_session)
    now = datetime.now(UTC)

    rows = await repository.get_timeseries(
        interval="day",
        category="Wildfires",
        start=now - timedelta(days=3),
        end=now,
    )
    assert sum(count for _, count in rows) == 2

    rows_by_source = await repository.get_timeseries(interval="day", source="other")
    assert sum(count for _, count in rows_by_source) == 1
