"""Tests for cleaned event validation."""

import pytest
from pydantic import ValidationError

from earthdata.processing.validation import CleanedEvent

VALID_PAYLOAD = {
    "id": "EONET_001",
    "title": "Wildfire - Somewhere",
    "categories": [{"id": 8, "title": "Wildfires"}],
    "geometry": [{"date": "2026-01-01T00:00:00Z", "type": "Point", "coordinates": [10.0, 20.0]}],
    "closed": None,
}


def test_cleaned_event_accepts_valid_payload() -> None:
    event = CleanedEvent.model_validate(VALID_PAYLOAD)

    assert event.id == "EONET_001"
    assert event.geometry[0].coordinates == [10.0, 20.0]


def test_cleaned_event_rejects_empty_categories() -> None:
    payload = {**VALID_PAYLOAD, "categories": []}

    with pytest.raises(ValidationError):
        CleanedEvent.model_validate(payload)


def test_cleaned_event_rejects_out_of_range_latitude() -> None:
    payload = {
        **VALID_PAYLOAD,
        "geometry": [
            {"date": "2026-01-01T00:00:00Z", "type": "Point", "coordinates": [10.0, 95.0]}
        ],
    }

    with pytest.raises(ValidationError):
        CleanedEvent.model_validate(payload)


def test_cleaned_event_rejects_out_of_range_longitude() -> None:
    payload = {
        **VALID_PAYLOAD,
        "geometry": [
            {"date": "2026-01-01T00:00:00Z", "type": "Point", "coordinates": [200.0, 10.0]}
        ],
    }

    with pytest.raises(ValidationError):
        CleanedEvent.model_validate(payload)
