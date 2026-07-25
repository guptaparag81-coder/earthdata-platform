"""Data cleaning for raw EONET event payloads."""

from __future__ import annotations

from typing import Any


def clean_event_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize a raw EONET event payload before validation.

    Trims whitespace from text fields, drops keys with `None`/empty values,
    and normalizes the geometry list to only the fields the pipeline needs.
    """
    cleaned: dict[str, Any] = {
        "id": str(payload.get("id", "")).strip(),
        "title": str(payload.get("title", "")).strip(),
        "categories": _clean_categories(payload.get("categories", [])),
        "geometry": _clean_geometry(payload.get("geometry", [])),
        "closed": payload.get("closed"),
    }
    return cleaned


def _clean_categories(categories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {"id": category.get("id"), "title": str(category.get("title", "")).strip()}
        for category in categories
        if category.get("title")
    ]


def _clean_geometry(geometry: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cleaned_points = []
    for point in geometry:
        coordinates = point.get("coordinates") or []
        if len(coordinates) < 2:
            continue
        cleaned_points.append(
            {
                "date": point.get("date"),
                "type": point.get("type", "Point"),
                "coordinates": coordinates[:3],
            }
        )
    return cleaned_points
