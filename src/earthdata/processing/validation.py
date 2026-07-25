"""Validation of cleaned event data prior to transformation."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class CleanedGeometryPoint(BaseModel):
    """A single validated geometry sample."""

    date: datetime
    type: str
    coordinates: list[float]


class CleanedCategory(BaseModel):
    """A single validated category classification.

    `id` accepts both the legacy integer form and EONET's current string
    slug form (e.g. `"wildfires"`); only `title` is used downstream.
    """

    id: int | str | None = None
    title: str


class CleanedEvent(BaseModel):
    """A cleaned EONET event, validated and ready for transformation.

    Enforces the domain invariants the processing pipeline relies on:
    a non-empty id/title, at least one category, at least one geometry
    point, and coordinates within valid Earth latitude/longitude ranges.
    """

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    categories: list[CleanedCategory] = Field(min_length=1)
    geometry: list[CleanedGeometryPoint] = Field(min_length=1)
    closed: datetime | None = None

    @field_validator("geometry")
    @classmethod
    def validate_coordinates(
        cls, geometry: list[CleanedGeometryPoint]
    ) -> list[CleanedGeometryPoint]:
        for point in geometry:
            longitude, latitude = point.coordinates[0], point.coordinates[1]
            if not (-180.0 <= longitude <= 180.0):
                raise ValueError(f"Longitude {longitude} out of range [-180, 180].")
            if not (-90.0 <= latitude <= 90.0):
                raise ValueError(f"Latitude {latitude} out of range [-90, 90].")
        return geometry
