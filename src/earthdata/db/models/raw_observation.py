"""ORM model for raw ingested Earth observation payloads."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from earthdata.db.base import Base


class RawObservation(Base):
    """A verbatim response captured from an upstream Earth observation source.

    Storing the raw payload preserves provenance and allows reprocessing if
    downstream transformation logic changes.
    """

    __tablename__ = "raw_observations"
    __table_args__ = (Index("ix_raw_observations_source_external_id", "source", "external_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    external_id: Mapped[str] = mapped_column(String(128), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"RawObservation(id={self.id!r}, source={self.source!r}, "
            f"external_id={self.external_id!r})"
        )
