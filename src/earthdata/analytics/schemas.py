"""API schemas for analytics and visualisation endpoints."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class TimeSeriesInterval(StrEnum):
    """Bucket granularity for time-series aggregation."""

    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class ExportFormat(StrEnum):
    """Supported export file formats."""

    JSON = "json"
    CSV = "csv"


class CategoryCount(BaseModel):
    """Number of processed observations in a given category."""

    category: str
    count: int


class SourceCount(BaseModel):
    """Number of processed observations from a given source."""

    source: str
    count: int


class SummaryStats(BaseModel):
    """Aggregate summary statistics across all processed observations."""

    total_count: int
    open_count: int
    closed_count: int
    by_category: list[CategoryCount]
    by_source: list[SourceCount]
    earliest_event_date: datetime | None
    latest_event_date: datetime | None


class TimeSeriesPoint(BaseModel):
    """A single bucketed count in a time series."""

    bucket_start: datetime
    count: int


class TimeSeriesResponse(BaseModel):
    """A time series of event counts bucketed by interval."""

    interval: TimeSeriesInterval
    points: list[TimeSeriesPoint]
