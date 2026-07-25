"""Processing service: cleans, validates, transforms, and stores observations."""

from __future__ import annotations

from pydantic import ValidationError

from earthdata.core.exceptions import DataValidationError
from earthdata.core.logging import get_logger
from earthdata.db.models.processed_observation import ProcessedObservation
from earthdata.db.models.raw_observation import RawObservation
from earthdata.processing.cleaning import clean_event_payload
from earthdata.processing.transformation import transform_to_processed_observation
from earthdata.processing.validation import CleanedEvent
from earthdata.repositories.processed_observation_repository import (
    ProcessedObservationRepository,
)
from earthdata.repositories.raw_observation_repository import RawObservationRepository

logger = get_logger(__name__)


class ProcessingService:
    """Orchestrates the clean -> validate -> transform -> store pipeline.

    Consumes `RawObservation` rows that have not yet been processed and
    produces corresponding `ProcessedObservation` rows.
    """

    def __init__(
        self,
        raw_repository: RawObservationRepository,
        processed_repository: ProcessedObservationRepository,
    ) -> None:
        self._raw_repository = raw_repository
        self._processed_repository = processed_repository

    async def process_pending(self, *, limit: int = 100) -> list[ProcessedObservation]:
        """Process all currently unprocessed raw observations.

        Records that fail validation are skipped and logged; one bad record
        does not abort processing of the remaining batch.
        """
        pending = await self._raw_repository.list_unprocessed(limit=limit)
        processed: list[ProcessedObservation] = []

        for raw in pending:
            try:
                processed.append(await self._process_one(raw))
            except DataValidationError as exc:
                logger.warning(
                    "raw_observation_skipped",
                    extra={"raw_observation_id": str(raw.id), "reason": exc.message},
                )

        logger.info(
            "processing_batch_completed",
            extra={"attempted": len(pending), "succeeded": len(processed)},
        )
        return processed

    async def _process_one(self, raw: RawObservation) -> ProcessedObservation:
        cleaned_payload = clean_event_payload(raw.payload)

        try:
            cleaned_event = CleanedEvent.model_validate(cleaned_payload)
        except ValidationError as exc:
            raise DataValidationError(
                f"Raw observation {raw.id} failed validation after cleaning.",
                details={"errors": exc.errors()},
            ) from exc

        processed_observation = transform_to_processed_observation(
            cleaned_event, raw_observation_id=raw.id, source=raw.source
        )
        return await self._processed_repository.upsert(processed_observation)
