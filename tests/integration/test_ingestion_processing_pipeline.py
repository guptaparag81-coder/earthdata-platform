"""End-to-end integration test: EONET ingestion -> processing, against a real database.

The external EONET API is mocked at the HTTP transport layer with `respx`;
everything else (HTTP client, services, repositories, PostgreSQL) is real.
"""

import httpx
import respx
from sqlalchemy.ext.asyncio import AsyncSession

from earthdata.ingestion.client import EonetClient
from earthdata.ingestion.service import IngestionService
from earthdata.processing.service import ProcessingService
from earthdata.repositories.processed_observation_repository import (
    ProcessedObservationRepository,
)
from earthdata.repositories.raw_observation_repository import RawObservationRepository

EONET_EVENTS_URL = "https://eonet.gsfc.nasa.gov/api/v3/events"

VALID_EVENT = {
    "id": "EONET_100",
    "title": "Wildfire - Integration Test",
    "categories": [{"id": 8, "title": "Wildfires"}],
    "geometry": [
        {"date": "2026-01-01T00:00:00Z", "type": "Point", "coordinates": [10.0, 20.0]},
        {"date": "2026-01-02T00:00:00Z", "type": "Point", "coordinates": [11.0, 21.0]},
    ],
    "closed": None,
}

INVALID_EVENT = {
    "id": "EONET_101",
    "title": "Missing categories",
    "categories": [{"id": 9, "title": "placeholder"}],
    "geometry": [{"date": "2026-01-01T00:00:00Z", "type": "Point", "coordinates": [999.0, 20.0]}],
    "closed": None,
}


@respx.mock
async def test_full_pipeline_ingest_then_process(db_session: AsyncSession) -> None:
    respx.get(EONET_EVENTS_URL).mock(
        return_value=httpx.Response(
            200, json={"title": "EONET Events", "events": [VALID_EVENT, INVALID_EVENT]}
        )
    )

    client = EonetClient(
        base_url="https://eonet.gsfc.nasa.gov/api/v3", timeout_seconds=5.0, max_retries=3
    )
    raw_repository = RawObservationRepository(db_session)
    processed_repository = ProcessedObservationRepository(db_session)

    ingestion_service = IngestionService(client=client, raw_repository=raw_repository)
    raw_records = await ingestion_service.ingest_events()
    await client.aclose()

    assert len(raw_records) == 2
    assert await raw_repository.count_filtered() == 2

    processing_service = ProcessingService(
        raw_repository=raw_repository, processed_repository=processed_repository
    )
    processed_records = await processing_service.process_pending()

    assert len(processed_records) == 1
    processed = processed_records[0]
    assert processed.external_id == "EONET_100"
    assert processed.category == "Wildfires"
    assert processed.latitude == 21.0
    assert processed.longitude == 11.0
    assert processed.is_open is True

    remaining_unprocessed = await raw_repository.list_unprocessed()
    assert {r.external_id for r in remaining_unprocessed} == {"EONET_101"}
