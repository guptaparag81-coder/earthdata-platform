"""Tests for the ingestion service."""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from earthdata.core.exceptions import DataValidationError
from earthdata.db.models.raw_observation import RawObservation
from earthdata.ingestion.service import IngestionService

EVENT_PAYLOAD = {
    "id": "EONET_001",
    "title": "Wildfire - Somewhere",
    "categories": [{"id": "wildfires", "title": "Wildfires"}],
    "geometry": [{"date": "2026-01-01T00:00:00Z", "type": "Point", "coordinates": [10.0, 20.0]}],
    "closed": None,
}

LEGACY_INT_CATEGORY_ID_PAYLOAD = {
    **EVENT_PAYLOAD,
    "id": "EONET_002",
    "categories": [{"id": 8, "title": "Wildfires"}],
}


class _FakeRawRepository:
    def __init__(self) -> None:
        self.bulk_add = AsyncMock(side_effect=lambda records: records)


@pytest.fixture
def raw_repository() -> _FakeRawRepository:
    return _FakeRawRepository()


async def test_ingest_events_stores_raw_records(raw_repository: _FakeRawRepository) -> None:
    client = AsyncMock()
    client.fetch_events.return_value = {"title": "EONET Events", "events": [EVENT_PAYLOAD]}

    service = IngestionService(client=client, raw_repository=raw_repository)  # type: ignore[arg-type]
    result = await service.ingest_events()

    assert len(result) == 1
    assert isinstance(result[0], RawObservation)
    assert result[0].external_id == "EONET_001"
    assert isinstance(result[0].fetched_at, datetime)
    raw_repository.bulk_add.assert_awaited_once()


async def test_ingest_events_accepts_legacy_integer_category_id(
    raw_repository: _FakeRawRepository,
) -> None:
    client = AsyncMock()
    client.fetch_events.return_value = {
        "title": "EONET Events",
        "events": [LEGACY_INT_CATEGORY_ID_PAYLOAD],
    }

    service = IngestionService(client=client, raw_repository=raw_repository)  # type: ignore[arg-type]
    result = await service.ingest_events()

    assert len(result) == 1
    assert result[0].external_id == "EONET_002"


async def test_ingest_events_returns_empty_list_when_no_events(
    raw_repository: _FakeRawRepository,
) -> None:
    client = AsyncMock()
    client.fetch_events.return_value = {"title": "EONET Events", "events": []}

    service = IngestionService(client=client, raw_repository=raw_repository)  # type: ignore[arg-type]
    result = await service.ingest_events()

    assert result == []
    raw_repository.bulk_add.assert_not_awaited()


async def test_ingest_events_raises_on_invalid_envelope(
    raw_repository: _FakeRawRepository,
) -> None:
    client = AsyncMock()
    client.fetch_events.return_value = {"events": [{"id": "missing_title_and_categories"}]}

    service = IngestionService(client=client, raw_repository=raw_repository)  # type: ignore[arg-type]

    with pytest.raises(DataValidationError):
        await service.ingest_events()
