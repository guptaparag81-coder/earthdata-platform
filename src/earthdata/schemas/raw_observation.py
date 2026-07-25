"""API schemas for raw observation records."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RawObservationCreate(BaseModel):
    """Payload for manually creating a raw observation record."""

    source: str = Field(min_length=1, max_length=64)
    external_id: str = Field(min_length=1, max_length=128)
    payload: dict[str, Any]
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class RawObservationRead(BaseModel):
    """A raw observation record as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source: str
    external_id: str
    payload: dict[str, Any]
    fetched_at: datetime
    created_at: datetime
