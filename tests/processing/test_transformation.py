"""Tests for transformation of cleaned events into processed observations."""

import uuid

from earthdata.processing.transformation import transform_to_processed_observation
from earthdata.processing.validation import CleanedEvent

PAYLOAD = {
    "id": "EONET_001",
    "title": "Wildfire - Somewhere",
    "categories": [{"id": 8, "title": "Wildfires"}, {"id": 9, "title": "Severe Storms"}],
    "geometry": [
        {"date": "2026-01-01T00:00:00Z", "type": "Point", "coordinates": [10.0, 20.0]},
        {"date": "2026-01-03T00:00:00Z", "type": "Point", "coordinates": [11.0, 21.0]},
    ],
    "closed": None,
}


def test_transform_uses_latest_geometry_and_primary_category() -> None:
    event = CleanedEvent.model_validate(PAYLOAD)
    raw_id = uuid.uuid4()

    processed = transform_to_processed_observation(event, raw_observation_id=raw_id, source="eonet")

    assert processed.external_id == "EONET_001"
    assert processed.category == "Wildfires"
    assert processed.longitude == 11.0
    assert processed.latitude == 21.0
    assert processed.is_open is True
    assert processed.raw_observation_id == raw_id


def test_transform_marks_closed_event_as_not_open() -> None:
    payload = {**PAYLOAD, "closed": "2026-01-05T00:00:00Z"}
    event = CleanedEvent.model_validate(payload)

    processed = transform_to_processed_observation(
        event, raw_observation_id=uuid.uuid4(), source="eonet"
    )

    assert processed.is_open is False
