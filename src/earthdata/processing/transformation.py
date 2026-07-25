"""Transformation of validated event data into persistable domain records."""

from __future__ import annotations

import uuid

from earthdata.db.models.processed_observation import ProcessedObservation
from earthdata.processing.validation import CleanedEvent


def transform_to_processed_observation(
    event: CleanedEvent, *, raw_observation_id: uuid.UUID, source: str
) -> ProcessedObservation:
    """Transform a validated `CleanedEvent` into a `ProcessedObservation` row.

    The most recent geometry sample is used as the event's canonical
    location, and the first listed category is used as its primary
    classification.
    """
    latest_point = max(event.geometry, key=lambda point: point.date)
    primary_category = event.categories[0]

    return ProcessedObservation(
        raw_observation_id=raw_observation_id,
        external_id=event.id,
        title=event.title,
        category=primary_category.title,
        source=source,
        event_date=latest_point.date,
        longitude=latest_point.coordinates[0],
        latitude=latest_point.coordinates[1],
        is_open=event.closed is None,
    )
