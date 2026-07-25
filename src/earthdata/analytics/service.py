"""Analytics service: aggregates processed observations for visualisation."""

from __future__ import annotations

from datetime import datetime

from earthdata.analytics.schemas import (
    CategoryCount,
    SourceCount,
    SummaryStats,
    TimeSeriesInterval,
    TimeSeriesPoint,
    TimeSeriesResponse,
)
from earthdata.repositories.processed_observation_repository import ProcessedObservationRepository
from earthdata.schemas.processed_observation import ProcessedObservationRead


class AnalyticsService:
    """Produces summary statistics, time series, and export data for the dashboard."""

    def __init__(self, repository: ProcessedObservationRepository) -> None:
        self._repository = repository

    async def get_summary(self) -> SummaryStats:
        """Compute aggregate summary statistics across all processed observations."""
        total = await self._repository.count_total()
        open_count = await self._repository.count_open()
        by_category_rows = await self._repository.count_by_category()
        by_source_rows = await self._repository.count_by_source()
        earliest, latest = await self._repository.get_event_date_bounds()

        return SummaryStats(
            total_count=total,
            open_count=open_count,
            closed_count=total - open_count,
            by_category=[
                CategoryCount(category=category, count=count)
                for category, count in by_category_rows
            ],
            by_source=[SourceCount(source=source, count=count) for source, count in by_source_rows],
            earliest_event_date=earliest,
            latest_event_date=latest,
        )

    async def get_timeseries(
        self,
        *,
        interval: TimeSeriesInterval,
        start: datetime | None = None,
        end: datetime | None = None,
        category: str | None = None,
        source: str | None = None,
    ) -> TimeSeriesResponse:
        """Compute event counts bucketed into the given time interval."""
        rows = await self._repository.get_timeseries(
            interval=interval.value,
            start=start,
            end=end,
            category=category,
            source=source,
        )
        points = [
            TimeSeriesPoint(bucket_start=bucket_start, count=count) for bucket_start, count in rows
        ]
        return TimeSeriesResponse(interval=interval, points=points)

    async def export_rows(
        self,
        *,
        category: str | None = None,
        source: str | None = None,
        is_open: bool | None = None,
        event_after: datetime | None = None,
        event_before: datetime | None = None,
        limit: int = 10_000,
    ) -> list[ProcessedObservationRead]:
        """Fetch processed observations matching the given filters for export."""
        instances = await self._repository.list_filtered(
            limit=limit,
            offset=0,
            category=category,
            source=source,
            is_open=is_open,
            event_after=event_after,
            event_before=event_before,
            sort_by="event_date",
            sort_order="asc",
        )
        return [ProcessedObservationRead.model_validate(instance) for instance in instances]
