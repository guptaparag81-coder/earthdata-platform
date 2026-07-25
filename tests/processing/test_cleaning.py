"""Tests for event payload cleaning."""

from earthdata.processing.cleaning import clean_event_payload


def test_clean_event_payload_trims_and_normalizes() -> None:
    raw = {
        "id": "  EONET_001  ",
        "title": "  Wildfire - Somewhere  ",
        "categories": [{"id": 8, "title": " Wildfires "}, {"id": 9, "title": ""}],
        "geometry": [
            {"date": "2026-01-01T00:00:00Z", "type": "Point", "coordinates": [10.0, 20.0]},
            {"date": "2026-01-02T00:00:00Z", "type": "Point", "coordinates": [10.0]},
        ],
        "closed": None,
    }

    cleaned = clean_event_payload(raw)

    assert cleaned["id"] == "EONET_001"
    assert cleaned["title"] == "Wildfire - Somewhere"
    assert cleaned["categories"] == [{"id": 8, "title": "Wildfires"}]
    assert len(cleaned["geometry"]) == 1
    assert cleaned["closed"] is None


def test_clean_event_payload_handles_missing_fields() -> None:
    cleaned = clean_event_payload({})

    assert cleaned["id"] == ""
    assert cleaned["title"] == ""
    assert cleaned["categories"] == []
    assert cleaned["geometry"] == []
