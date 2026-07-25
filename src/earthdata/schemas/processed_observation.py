"""API schemas for processed observation records."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProcessedObservationCreate(BaseModel):
    """Payload for manually creating a processed observation record."""

    raw_observation_id: uuid.UUID
    external_id: str = Field(min_length=1, max_length=128)
    title: str = Field(min_length=1, max_length=512)
    category: str = Field(min_length=1, max_length=128)
    source: str = Field(min_length=1, max_length=64)
    event_date: datetime
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    is_open: bool = True


class ProcessedObservationUpdate(BaseModel):
    """Partial update payload for a processed observation record."""

    title: str | None = Field(default=None, min_length=1, max_length=512)
    category: str | None = Field(default=None, min_length=1, max_length=128)
    event_date: datetime | None = None
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0)
    is_open: bool | None = None


class ProcessedObservationRead(BaseModel):
    """A processed observation record as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    raw_observation_id: uuid.UUID
    external_id: str
    title: str
    category: str
    source: str
    event_date: datetime
    latitude: float
    longitude: float
    is_open: bool
    created_at: datetime
    updated_at: datetime
