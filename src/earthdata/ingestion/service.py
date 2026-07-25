"""Ingestion service: fetches and persists raw Earth observation data."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import ValidationError

from earthdata.core.exceptions import DataValidationError
from earthdata.core.logging import get_logger
from earthdata.db.models.raw_observation import RawObservation
from earthdata.ingestion.client import EonetClient
from earthdata.ingestion.schemas import EonetEventsResponse
from earthdata.repositories.raw_observation_repository import RawObservationRepository

logger = get_logger(__name__)

SOURCE_NAME = "eonet"


class IngestionService:
    """Orchestrates fetching Earth observation events and storing them raw.

    Validation here confirms the upstream payload has the shape the
    processing layer expects; it does not mutate the payload, which is
    stored verbatim for provenance.
    """

    def __init__(self, client: EonetClient, raw_repository: RawObservationRepository) -> None:
        self._client = client
        self._raw_repository = raw_repository

    async def ingest_events(
        self, *, status: str = "open", limit: int = 50, days: int | None = None
    ) -> list[RawObservation]:
        """Fetch events from EONET, validate the envelope, and store each raw record.

        Returns:
            The persisted `RawObservation` rows, one per event in the response.

        Raises:
            DataValidationError: If the upstream payload does not match the
                expected EONET schema.
        """
        payload = await self._client.fetch_events(status=status, limit=limit, days=days)

        try:
            validated = EonetEventsResponse.model_validate(payload)
        except ValidationError as exc:
            logger.error("eonet_payload_invalid", extra={"error": str(exc)})
            raise DataValidationError(
                "Upstream EONET response failed schema validation.",
                details={"errors": exc.errors()},
            ) from exc

        fetched_at = datetime.now(UTC)
        raw_records = [
            RawObservation(
                source=SOURCE_NAME,
                external_id=event.id,
                payload=payload["events"][index],
                fetched_at=fetched_at,
            )
            for index, event in enumerate(validated.events)
        ]

        if not raw_records:
            logger.info("eonet_ingest_empty", extra={"status": status})
            return []

        persisted = await self._raw_repository.bulk_add(raw_records)
        logger.info("eonet_ingest_completed", extra={"count": len(persisted)})
        return persisted
