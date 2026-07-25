"""CSV export helpers for processed observation data."""

from __future__ import annotations

import csv
import io

from earthdata.schemas.processed_observation import ProcessedObservationRead

CSV_FIELDS = [
    "id",
    "raw_observation_id",
    "external_id",
    "title",
    "category",
    "source",
    "event_date",
    "latitude",
    "longitude",
    "is_open",
    "created_at",
    "updated_at",
]


def to_csv(rows: list[ProcessedObservationRead]) -> str:
    """Serialize processed observations to CSV text with a header row."""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_FIELDS)
    writer.writeheader()
    for row in rows:
        data = row.model_dump(mode="json")
        writer.writerow({field: data[field] for field in CSV_FIELDS})
    return buffer.getvalue()
