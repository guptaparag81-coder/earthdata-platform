"""Pydantic schemas for validating upstream EONET API payloads."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EonetCategory(BaseModel):
    """A category classification attached to an EONET event."""

    model_config = ConfigDict(extra="ignore")

    id: int
    title: str


class EonetGeometry(BaseModel):
    """A single geometry sample (point-in-time location) of an EONET event."""

    model_config = ConfigDict(extra="ignore")

    date: datetime
    type: str
    coordinates: list[float] = Field(min_length=2, max_length=3)


class EonetEvent(BaseModel):
    """A single natural event as returned by the EONET `/events` endpoint."""

    model_config = ConfigDict(extra="ignore")

    id: str
    title: str
    categories: list[EonetCategory] = Field(min_length=1)
    geometry: list[EonetGeometry] = Field(min_length=1)
    closed: datetime | None = None


class EonetEventsResponse(BaseModel):
    """The top-level EONET `/events` response envelope."""

    model_config = ConfigDict(extra="ignore")

    title: str
    events: list[EonetEvent]
