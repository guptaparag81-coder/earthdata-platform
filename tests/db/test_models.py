"""Tests for ORM model `__repr__` implementations."""

import uuid
from datetime import UTC, datetime

from earthdata.db.models.processed_observation import ProcessedObservation
from earthdata.db.models.raw_observation import RawObservation


def test_raw_observation_repr() -> None:
    instance = RawObservation(
        id=uuid.uuid4(),
        source="eonet",
        external_id="EONET_001",
        payload={"id": "EONET_001"},
        fetched_at=datetime.now(UTC),
    )

    text = repr(instance)

    assert "RawObservation" in text
    assert "eonet" in text
    assert "EONET_001" in text


def test_processed_observation_repr() -> None:
    instance = ProcessedObservation(
        id=uuid.uuid4(),
        raw_observation_id=uuid.uuid4(),
        external_id="EONET_001",
        title="Wildfire",
        category="Wildfires",
        source="eonet",
        event_date=datetime.now(UTC),
        latitude=1.0,
        longitude=2.0,
        is_open=True,
    )

    text = repr(instance)

    assert "ProcessedObservation" in text
    assert "EONET_001" in text
    assert "Wildfires" in text
