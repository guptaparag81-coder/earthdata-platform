"""Tests for `RawObservationRepository` query methods."""

from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from earthdata.db.models.processed_observation import ProcessedObservation
from earthdata.db.models.raw_observation import RawObservation
from earthdata.repositories.processed_observation_repository import (
    ProcessedObservationRepository,
)
from earthdata.repositories.raw_observation_repository import RawObservationRepository


async def _seed(session: AsyncSession) -> RawObservationRepository:
    repository = RawObservationRepository(session)
    now = datetime.now(UTC)
    await repository.add(
        RawObservation(
            source="eonet",
            external_id="A1",
            payload={"id": "A1"},
            fetched_at=now - timedelta(days=2),
        )
    )
    await repository.add(
        RawObservation(
            source="eonet",
            external_id="A2",
            payload={"id": "A2"},
            fetched_at=now - timedelta(days=1),
        )
    )
    await repository.add(
        RawObservation(
            source="other",
            external_id="B1",
            payload={"id": "B1"},
            fetched_at=now,
        )
    )
    return repository


async def test_get_by_source_and_external_id_found_and_missing(db_session: AsyncSession) -> None:
    repository = await _seed(db_session)

    found = await repository.get_by_source_and_external_id("eonet", "A1")
    assert found is not None
    assert found.external_id == "A1"

    missing = await repository.get_by_source_and_external_id("eonet", "does-not-exist")
    assert missing is None


async def test_list_filtered_by_source(db_session: AsyncSession) -> None:
    repository = await _seed(db_session)

    results = await repository.list_filtered(limit=10, offset=0, source="eonet")
    assert {r.external_id for r in results} == {"A1", "A2"}


async def test_list_filtered_by_external_id(db_session: AsyncSession) -> None:
    repository = await _seed(db_session)

    results = await repository.list_filtered(limit=10, offset=0, external_id="B1")
    assert [r.external_id for r in results] == ["B1"]


async def test_list_filtered_by_fetched_range(db_session: AsyncSession) -> None:
    repository = await _seed(db_session)
    now = datetime.now(UTC)

    results = await repository.list_filtered(
        limit=10,
        offset=0,
        fetched_after=now - timedelta(days=1, hours=1),
        fetched_before=now - timedelta(hours=1),
    )
    assert [r.external_id for r in results] == ["A2"]


async def test_list_filtered_sort_order(db_session: AsyncSession) -> None:
    repository = await _seed(db_session)

    desc = await repository.list_filtered(
        limit=10, offset=0, sort_by="fetched_at", sort_order="desc"
    )
    asc = await repository.list_filtered(limit=10, offset=0, sort_by="fetched_at", sort_order="asc")

    assert [r.external_id for r in desc] == ["B1", "A2", "A1"]
    assert [r.external_id for r in asc] == ["A1", "A2", "B1"]


async def test_list_filtered_pagination(db_session: AsyncSession) -> None:
    repository = await _seed(db_session)

    page_1 = await repository.list_filtered(
        limit=2, offset=0, sort_by="fetched_at", sort_order="asc"
    )
    page_2 = await repository.list_filtered(
        limit=2, offset=2, sort_by="fetched_at", sort_order="asc"
    )

    assert [r.external_id for r in page_1] == ["A1", "A2"]
    assert [r.external_id for r in page_2] == ["B1"]


async def test_count_filtered(db_session: AsyncSession) -> None:
    repository = await _seed(db_session)

    assert await repository.count_filtered() == 3
    assert await repository.count_filtered(source="eonet") == 2
    assert await repository.count_filtered(source="does-not-exist") == 0


async def test_list_unprocessed_excludes_processed_records(db_session: AsyncSession) -> None:
    raw_repository = await _seed(db_session)
    processed_repository = ProcessedObservationRepository(db_session)

    a1 = await raw_repository.get_by_source_and_external_id("eonet", "A1")
    assert a1 is not None

    await processed_repository.upsert(
        ProcessedObservation(
            raw_observation_id=a1.id,
            external_id="A1",
            title="Processed A1",
            category="Wildfires",
            source="eonet",
            event_date=datetime.now(UTC),
            latitude=1.0,
            longitude=2.0,
            is_open=True,
        )
    )

    unprocessed = await raw_repository.list_unprocessed(limit=10)
    assert {r.external_id for r in unprocessed} == {"A2", "B1"}
