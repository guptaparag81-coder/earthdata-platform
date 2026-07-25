"""Tests for the generic `BaseRepository` CRUD operations."""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from earthdata.db.models.raw_observation import RawObservation
from earthdata.repositories.raw_observation_repository import RawObservationRepository


def _make_raw(source: str = "eonet", external_id: str = "EONET_001") -> dict[str, Any]:
    return {
        "source": source,
        "external_id": external_id,
        "payload": {"id": external_id},
        "fetched_at": datetime.now(UTC),
    }


async def test_add_and_get_by_id(db_session: AsyncSession) -> None:
    repository = RawObservationRepository(db_session)
    instance = RawObservation(**_make_raw())

    created = await repository.add(instance)
    fetched = await repository.get_by_id(created.id)

    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.external_id == "EONET_001"


async def test_get_by_id_returns_none_when_missing(db_session: AsyncSession) -> None:
    repository = RawObservationRepository(db_session)

    assert await repository.get_by_id(uuid.uuid4()) is None


async def test_list_all_paginates(db_session: AsyncSession) -> None:
    repository = RawObservationRepository(db_session)
    for i in range(5):
        await repository.add(RawObservation(**_make_raw(external_id=f"EONET_{i}")))

    page = await repository.list_all(limit=2, offset=0)
    assert len(page) == 2

    all_records = await repository.list_all(limit=100, offset=0)
    assert len(all_records) == 5


async def test_bulk_add(db_session: AsyncSession) -> None:
    repository = RawObservationRepository(db_session)
    instances = [RawObservation(**_make_raw(external_id=f"BULK_{i}")) for i in range(3)]

    created = await repository.bulk_add(instances)

    assert len(created) == 3
    all_records = await repository.list_all(limit=100)
    assert len(all_records) == 3


async def test_update_flushes_in_place_changes(db_session: AsyncSession) -> None:
    repository = RawObservationRepository(db_session)
    instance = await repository.add(RawObservation(**_make_raw()))

    instance.source = "modified"
    updated = await repository.update(instance)

    assert updated.source == "modified"
    fetched = await repository.get_by_id(instance.id)
    assert fetched is not None
    assert fetched.source == "modified"


async def test_delete_removes_record(db_session: AsyncSession) -> None:
    repository = RawObservationRepository(db_session)
    instance = await repository.add(RawObservation(**_make_raw()))

    await repository.delete(instance)

    assert await repository.get_by_id(instance.id) is None
