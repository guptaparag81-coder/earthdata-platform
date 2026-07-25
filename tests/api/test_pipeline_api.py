"""API tests for the ingestion/processing pipeline trigger endpoints.

These exercise the full dependency-injection chain (settings -> EONET client
-> ingestion/processing services -> repositories -> real database), mocking
only the external EONET HTTP call via `respx`.
"""

import httpx
import respx
from httpx import AsyncClient

EONET_EVENTS_URL = "https://eonet.gsfc.nasa.gov/api/v3/events"

EVENT_PAYLOAD = {
    "id": "EONET_001",
    "title": "Wildfire - Somewhere",
    "categories": [{"id": "wildfires", "title": "Wildfires"}],
    "geometry": [{"date": "2026-01-01T00:00:00Z", "type": "Point", "coordinates": [10.0, 20.0]}],
    "closed": None,
}


@respx.mock
async def test_trigger_ingestion_stores_raw_observations(db_client: AsyncClient) -> None:
    respx.get(EONET_EVENTS_URL).mock(
        return_value=httpx.Response(200, json={"title": "EONET Events", "events": [EVENT_PAYLOAD]})
    )

    response = await db_client.post("/api/v1/pipeline/ingest")

    assert response.status_code == 201
    body = response.json()
    assert body["ingested_count"] == 1
    assert body["observations"][0]["external_id"] == "EONET_001"


@respx.mock
async def test_trigger_ingestion_raises_upstream_error_on_persistent_failure(
    db_client: AsyncClient,
) -> None:
    respx.get(EONET_EVENTS_URL).mock(return_value=httpx.Response(503))

    response = await db_client.post("/api/v1/pipeline/ingest")

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "upstream_service_error"


@respx.mock
async def test_trigger_ingestion_rejects_invalid_upstream_payload(db_client: AsyncClient) -> None:
    respx.get(EONET_EVENTS_URL).mock(return_value=httpx.Response(200, json={"events": []}))

    response = await db_client.post("/api/v1/pipeline/ingest")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "data_validation_error"


@respx.mock
async def test_trigger_processing_processes_pending_raw_observations(
    db_client: AsyncClient,
) -> None:
    respx.get(EONET_EVENTS_URL).mock(
        return_value=httpx.Response(200, json={"title": "EONET Events", "events": [EVENT_PAYLOAD]})
    )
    await db_client.post("/api/v1/pipeline/ingest")

    response = await db_client.post("/api/v1/pipeline/process")

    assert response.status_code == 200
    body = response.json()
    assert body["processed_count"] == 1
    assert body["observations"][0]["external_id"] == "EONET_001"
    assert body["observations"][0]["category"] == "Wildfires"


async def test_trigger_processing_with_nothing_pending(db_client: AsyncClient) -> None:
    response = await db_client.post("/api/v1/pipeline/process")

    assert response.status_code == 200
    assert response.json() == {"processed_count": 0, "observations": []}
