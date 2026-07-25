"""Tests for the processing service."""

import uuid
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock

from earthdata.db.models.processed_observation import ProcessedObservation
from earthdata.db.models.raw_observation import RawObservation
from earthdata.processing.service import ProcessingService

VALID_PAYLOAD = {
    "id": "EONET_001",
    "title": "Wildfire - Somewhere",
    "categories": [{"id": 8, "title": "Wildfires"}],
    "geometry": [{"date": "2026-01-01T00:00:00Z", "type": "Point", "coordinates": [10.0, 20.0]}],
    "closed": None,
}

INVALID_PAYLOAD = {"id": "EONET_002", "title": "", "categories": [], "geometry": []}


def _make_raw(payload: dict[str, Any]) -> RawObservation:
    return RawObservation(
        id=uuid.uuid4(),
        source="eonet",
        external_id=payload["id"],
        payload=payload,
        fetched_at=datetime.now(UTC),
    )


async def test_process_pending_skips_invalid_and_processes_valid() -> None:
    good_raw = _make_raw(VALID_PAYLOAD)
    bad_raw = _make_raw(INVALID_PAYLOAD)

    raw_repository = AsyncMock()
    raw_repository.list_unprocessed.return_value = [good_raw, bad_raw]

    processed_repository = AsyncMock()
    processed_repository.upsert.side_effect = lambda instance: instance

    service = ProcessingService(
        raw_repository=raw_repository, processed_repository=processed_repository
    )

    results = await service.process_pending()

    assert len(results) == 1
    assert isinstance(results[0], ProcessedObservation)
    assert results[0].external_id == "EONET_001"
    processed_repository.upsert.assert_awaited_once()


async def test_process_pending_returns_empty_when_nothing_pending() -> None:
    raw_repository = AsyncMock()
    raw_repository.list_unprocessed.return_value = []
    processed_repository = AsyncMock()

    service = ProcessingService(
        raw_repository=raw_repository, processed_repository=processed_repository
    )

    results = await service.process_pending()

    assert results == []
    processed_repository.upsert.assert_not_awaited()
