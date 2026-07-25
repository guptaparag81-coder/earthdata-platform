"""Endpoints that trigger the ingestion and processing pipelines."""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Query, status
from pydantic import BaseModel

from earthdata.core.di import IngestionServiceDep, ProcessingServiceDep
from earthdata.schemas.processed_observation import ProcessedObservationRead
from earthdata.schemas.raw_observation import RawObservationRead

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


class IngestResult(BaseModel):
    """Outcome of triggering an EONET ingestion run."""

    ingested_count: int
    observations: list[RawObservationRead]


class ProcessResult(BaseModel):
    """Outcome of triggering a processing run over pending raw observations."""

    processed_count: int
    observations: list[ProcessedObservationRead]


@router.post(
    "/ingest",
    response_model=IngestResult,
    status_code=status.HTTP_201_CREATED,
    summary="Fetch Earth observation events from EONET and store them raw",
)
async def trigger_ingestion(
    service: IngestionServiceDep,
    status_filter: Annotated[Literal["open", "closed", "all"], Query(alias="status")] = "open",
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    days: Annotated[int | None, Query(ge=1, le=365)] = None,
) -> IngestResult:
    """Trigger an on-demand EONET ingestion run and persist the raw payloads."""
    records = await service.ingest_events(status=status_filter, limit=limit, days=days)
    return IngestResult(
        ingested_count=len(records),
        observations=[RawObservationRead.model_validate(record) for record in records],
    )


@router.post(
    "/process",
    response_model=ProcessResult,
    summary="Clean, validate, and transform pending raw observations",
)
async def trigger_processing(
    service: ProcessingServiceDep,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> ProcessResult:
    """Trigger processing of raw observations that have not yet been processed."""
    records = await service.process_pending(limit=limit)
    return ProcessResult(
        processed_count=len(records),
        observations=[ProcessedObservationRead.model_validate(record) for record in records],
    )
