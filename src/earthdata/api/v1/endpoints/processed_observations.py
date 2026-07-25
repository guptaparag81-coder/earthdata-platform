"""CRUD endpoints for processed observation records."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Query, status

from earthdata.core.di import ProcessedRepositoryDep
from earthdata.core.exceptions import RecordNotFoundError
from earthdata.db.models.processed_observation import ProcessedObservation
from earthdata.repositories.processed_observation_repository import ProcessedSortField
from earthdata.schemas.common import Page, SortOrder
from earthdata.schemas.processed_observation import (
    ProcessedObservationCreate,
    ProcessedObservationRead,
    ProcessedObservationUpdate,
)

router = APIRouter(prefix="/processed-observations", tags=["processed-observations"])


async def _get_or_404(
    repository: ProcessedRepositoryDep, observation_id: uuid.UUID
) -> ProcessedObservation:
    instance = await repository.get_by_id(observation_id)
    if instance is None:
        raise RecordNotFoundError(f"Processed observation {observation_id} was not found.")
    return instance


@router.get(
    "",
    response_model=Page[ProcessedObservationRead],
    summary="List processed observations",
    description="List processed observation records with pagination, filtering, and sorting.",
)
async def list_processed_observations(
    repository: ProcessedRepositoryDep,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    category: Annotated[str | None, Query(max_length=128)] = None,
    source: Annotated[str | None, Query(max_length=64)] = None,
    is_open: bool | None = None,
    external_id: Annotated[str | None, Query(max_length=128)] = None,
    event_after: datetime | None = None,
    event_before: datetime | None = None,
    sort_by: ProcessedSortField = "event_date",
    sort_order: SortOrder = SortOrder.DESC,
) -> Page[ProcessedObservationRead]:
    """Return a filtered, sorted, paginated page of processed observations."""
    items = await repository.list_filtered(
        limit=limit,
        offset=offset,
        category=category,
        source=source,
        is_open=is_open,
        external_id=external_id,
        event_after=event_after,
        event_before=event_before,
        sort_by=sort_by,
        sort_order=sort_order.value,
    )
    total = await repository.count_filtered(
        category=category,
        source=source,
        is_open=is_open,
        external_id=external_id,
        event_after=event_after,
        event_before=event_before,
    )
    return Page[ProcessedObservationRead](
        items=[ProcessedObservationRead.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{observation_id}",
    response_model=ProcessedObservationRead,
    summary="Get a processed observation by id",
)
async def get_processed_observation(
    observation_id: uuid.UUID, repository: ProcessedRepositoryDep
) -> ProcessedObservation:
    """Fetch a single processed observation by its primary key."""
    return await _get_or_404(repository, observation_id)


@router.post(
    "",
    response_model=ProcessedObservationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a processed observation",
)
async def create_processed_observation(
    payload: ProcessedObservationCreate, repository: ProcessedRepositoryDep
) -> ProcessedObservation:
    """Create and persist a new processed observation record."""
    instance = ProcessedObservation(**payload.model_dump())
    return await repository.add(instance)


@router.patch(
    "/{observation_id}",
    response_model=ProcessedObservationRead,
    summary="Partially update a processed observation",
)
async def update_processed_observation(
    observation_id: uuid.UUID,
    payload: ProcessedObservationUpdate,
    repository: ProcessedRepositoryDep,
) -> ProcessedObservation:
    """Apply a partial update to an existing processed observation."""
    instance = await _get_or_404(repository, observation_id)
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(instance, field, value)
    return await repository.update(instance)


@router.delete(
    "/{observation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a processed observation",
)
async def delete_processed_observation(
    observation_id: uuid.UUID, repository: ProcessedRepositoryDep
) -> None:
    """Delete a processed observation record by id."""
    instance = await _get_or_404(repository, observation_id)
    await repository.delete(instance)
