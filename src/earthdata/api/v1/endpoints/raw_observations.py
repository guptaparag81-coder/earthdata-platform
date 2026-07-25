"""CRUD endpoints for raw observation records."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Query, status

from earthdata.core.di import RawRepositoryDep
from earthdata.core.exceptions import RecordNotFoundError
from earthdata.db.models.raw_observation import RawObservation
from earthdata.repositories.raw_observation_repository import RawSortField
from earthdata.schemas.common import Page, SortOrder
from earthdata.schemas.raw_observation import RawObservationCreate, RawObservationRead

router = APIRouter(prefix="/raw-observations", tags=["raw-observations"])


async def _get_or_404(repository: RawRepositoryDep, observation_id: uuid.UUID) -> RawObservation:
    instance = await repository.get_by_id(observation_id)
    if instance is None:
        raise RecordNotFoundError(f"Raw observation {observation_id} was not found.")
    return instance


@router.get(
    "",
    response_model=Page[RawObservationRead],
    summary="List raw observations",
    description="List raw observation records with pagination, filtering, and sorting.",
)
async def list_raw_observations(
    repository: RawRepositoryDep,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    source: Annotated[str | None, Query(max_length=64)] = None,
    external_id: Annotated[str | None, Query(max_length=128)] = None,
    fetched_after: datetime | None = None,
    fetched_before: datetime | None = None,
    sort_by: RawSortField = "created_at",
    sort_order: SortOrder = SortOrder.DESC,
) -> Page[RawObservationRead]:
    """Return a filtered, sorted, paginated page of raw observations."""
    items = await repository.list_filtered(
        limit=limit,
        offset=offset,
        source=source,
        external_id=external_id,
        fetched_after=fetched_after,
        fetched_before=fetched_before,
        sort_by=sort_by,
        sort_order=sort_order.value,
    )
    total = await repository.count_filtered(
        source=source,
        external_id=external_id,
        fetched_after=fetched_after,
        fetched_before=fetched_before,
    )
    return Page[RawObservationRead](
        items=[RawObservationRead.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{observation_id}",
    response_model=RawObservationRead,
    summary="Get a raw observation by id",
)
async def get_raw_observation(
    observation_id: uuid.UUID, repository: RawRepositoryDep
) -> RawObservation:
    """Fetch a single raw observation by its primary key."""
    return await _get_or_404(repository, observation_id)


@router.post(
    "",
    response_model=RawObservationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a raw observation",
    description="Manually store a raw observation payload (e.g. for backfill).",
)
async def create_raw_observation(
    payload: RawObservationCreate, repository: RawRepositoryDep
) -> RawObservation:
    """Create and persist a new raw observation record."""
    instance = RawObservation(
        source=payload.source,
        external_id=payload.external_id,
        payload=payload.payload,
        fetched_at=payload.fetched_at,
    )
    return await repository.add(instance)


@router.delete(
    "/{observation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a raw observation",
)
async def delete_raw_observation(observation_id: uuid.UUID, repository: RawRepositoryDep) -> None:
    """Delete a raw observation record by id."""
    instance = await _get_or_404(repository, observation_id)
    await repository.delete(instance)
