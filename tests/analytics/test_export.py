"""Tests for CSV export of processed observations."""

import uuid
from datetime import UTC, datetime

from earthdata.analytics.export import CSV_FIELDS, to_csv
from earthdata.schemas.processed_observation import ProcessedObservationRead


def _make_row() -> ProcessedObservationRead:
    now = datetime.now(UTC)
    return ProcessedObservationRead(
        id=uuid.uuid4(),
        raw_observation_id=uuid.uuid4(),
        external_id="W1",
        title="Wildfire - Somewhere",
        category="Wildfires",
        source="eonet",
        event_date=now,
        latitude=10.0,
        longitude=20.0,
        is_open=True,
        created_at=now,
        updated_at=now,
    )


def test_to_csv_includes_header_and_row() -> None:
    csv_text = to_csv([_make_row()])
    lines = csv_text.strip().splitlines()

    assert lines[0] == ",".join(CSV_FIELDS)
    assert "W1" in lines[1]
    assert "Wildfires" in lines[1]


def test_to_csv_empty_list_returns_only_header() -> None:
    csv_text = to_csv([])
    lines = csv_text.strip().splitlines()

    assert lines == [",".join(CSV_FIELDS)]
