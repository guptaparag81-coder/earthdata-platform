"""Analytics endpoints: summary statistics, time series, and data export."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Query
from fastapi.responses import PlainTextResponse

from earthdata.analytics.export import to_csv
from earthdata.analytics.schemas import (
    ExportFormat,
    SummaryStats,
    TimeSeriesInterval,
    TimeSeriesResponse,
)
from earthdata.core.di import AnalyticsServiceDep
from earthdata.schemas.processed_observation import ProcessedObservationRead

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get(
    "/summary",
    response_model=SummaryStats,
    summary="Summary statistics across processed observations",
)
async def get_summary(service: AnalyticsServiceDep) -> SummaryStats:
    """Return aggregate counts, category/source breakdowns, and date bounds."""
    return await service.get_summary()


@router.get(
    "/timeseries",
    response_model=TimeSeriesResponse,
    summary="Event counts bucketed over time",
)
async def get_timeseries(
    service: AnalyticsServiceDep,
    interval: TimeSeriesInterval = TimeSeriesInterval.DAY,
    start: datetime | None = None,
    end: datetime | None = None,
    category: Annotated[str | None, Query(max_length=128)] = None,
    source: Annotated[str | None, Query(max_length=64)] = None,
) -> TimeSeriesResponse:
    """Return a time series of event counts bucketed by day, week, or month."""
    return await service.get_timeseries(
        interval=interval, start=start, end=end, category=category, source=source
    )


@router.get(
    "/export",
    response_model=None,
    summary="Export processed observations as JSON or CSV",
)
async def export_observations(
    service: AnalyticsServiceDep,
    export_format: Annotated[ExportFormat, Query(alias="format")] = ExportFormat.JSON,
    category: Annotated[str | None, Query(max_length=128)] = None,
    source: Annotated[str | None, Query(max_length=64)] = None,
    is_open: bool | None = None,
    event_after: datetime | None = None,
    event_before: datetime | None = None,
    limit: Annotated[int, Query(ge=1, le=10_000)] = 1000,
) -> list[ProcessedObservationRead] | PlainTextResponse:
    """Export processed observations matching the given filters as JSON or CSV."""
    rows = await service.export_rows(
        category=category,
        source=source,
        is_open=is_open,
        event_after=event_after,
        event_before=event_before,
        limit=limit,
    )

    if export_format is ExportFormat.CSV:
        return PlainTextResponse(
            content=to_csv(rows),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=processed_observations.csv"},
        )

    return rows
