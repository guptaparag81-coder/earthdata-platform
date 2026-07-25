"""Dependency injection wiring for the application.

FastAPI's `Depends` mechanism is used as the DI container. This module
centralizes provider functions so that concrete implementations can be
swapped (e.g. in tests) without touching call sites.
"""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from earthdata.analytics.service import AnalyticsService
from earthdata.core.config import Settings, get_settings
from earthdata.db.session import get_session_factory
from earthdata.ingestion.client import EonetClient
from earthdata.ingestion.service import IngestionService
from earthdata.processing.service import ProcessingService
from earthdata.repositories.processed_observation_repository import (
    ProcessedObservationRepository,
)
from earthdata.repositories.raw_observation_repository import RawObservationRepository

SettingsDep = Annotated[Settings, Depends(get_settings)]


async def get_db_session(
    settings: SettingsDep,
) -> AsyncGenerator[AsyncSession]:
    """Yield a request-scoped database session.

    Acts as a per-request unit of work: commits on clean completion of the
    request, rolls back if the endpoint or a downstream layer raises.
    """
    session_factory = get_session_factory(settings)
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


DbSessionDep = Annotated[AsyncSession, Depends(get_db_session)]


def get_eonet_client(settings: SettingsDep) -> EonetClient:
    """Provide an `EonetClient` configured from application settings."""
    return EonetClient(
        base_url=settings.eonet_base_url,
        timeout_seconds=settings.eonet_timeout_seconds,
        max_retries=settings.eonet_max_retries,
    )


EonetClientDep = Annotated[EonetClient, Depends(get_eonet_client)]


def get_raw_observation_repository(session: DbSessionDep) -> RawObservationRepository:
    """Provide a `RawObservationRepository` bound to the request session."""
    return RawObservationRepository(session)


RawRepositoryDep = Annotated[RawObservationRepository, Depends(get_raw_observation_repository)]


def get_processed_observation_repository(
    session: DbSessionDep,
) -> ProcessedObservationRepository:
    """Provide a `ProcessedObservationRepository` bound to the request session."""
    return ProcessedObservationRepository(session)


ProcessedRepositoryDep = Annotated[
    ProcessedObservationRepository, Depends(get_processed_observation_repository)
]


def get_ingestion_service(
    client: EonetClientDep,
    raw_repository: RawRepositoryDep,
) -> IngestionService:
    """Provide an `IngestionService` with its collaborators wired in."""
    return IngestionService(client=client, raw_repository=raw_repository)


IngestionServiceDep = Annotated[IngestionService, Depends(get_ingestion_service)]


def get_processing_service(
    raw_repository: RawRepositoryDep,
    processed_repository: ProcessedRepositoryDep,
) -> ProcessingService:
    """Provide a `ProcessingService` with its collaborators wired in."""
    return ProcessingService(
        raw_repository=raw_repository,
        processed_repository=processed_repository,
    )


ProcessingServiceDep = Annotated[ProcessingService, Depends(get_processing_service)]


def get_analytics_service(processed_repository: ProcessedRepositoryDep) -> AnalyticsService:
    """Provide an `AnalyticsService` bound to the processed observation repository."""
    return AnalyticsService(processed_repository)


AnalyticsServiceDep = Annotated[AnalyticsService, Depends(get_analytics_service)]


__all__ = [
    "AnalyticsServiceDep",
    "DbSessionDep",
    "EonetClientDep",
    "IngestionServiceDep",
    "ProcessedRepositoryDep",
    "ProcessingServiceDep",
    "RawRepositoryDep",
    "SettingsDep",
    "get_analytics_service",
    "get_db_session",
    "get_eonet_client",
    "get_ingestion_service",
    "get_processed_observation_repository",
    "get_processing_service",
    "get_raw_observation_repository",
]
