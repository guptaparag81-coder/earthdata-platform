"""Tests for the EONET async HTTP client."""

import httpx
import pytest
import respx

from earthdata.core.exceptions import UpstreamServiceError
from earthdata.ingestion.client import EonetClient

BASE_URL = "https://eonet.gsfc.nasa.gov/api/v3"


@pytest.fixture
async def client() -> EonetClient:
    return EonetClient(base_url=BASE_URL, timeout_seconds=5.0, max_retries=3)


@respx.mock
async def test_fetch_events_returns_payload(client: EonetClient) -> None:
    respx.get(f"{BASE_URL}/events").mock(
        return_value=httpx.Response(200, json={"title": "EONET Events", "events": []})
    )

    payload = await client.fetch_events()

    assert payload["title"] == "EONET Events"
    await client.aclose()


@respx.mock
async def test_fetch_events_retries_on_server_error_then_succeeds(client: EonetClient) -> None:
    route = respx.get(f"{BASE_URL}/events")
    route.side_effect = [
        httpx.Response(503),
        httpx.Response(200, json={"title": "EONET Events", "events": []}),
    ]

    payload = await client.fetch_events()

    assert payload["title"] == "EONET Events"
    assert route.call_count == 2
    await client.aclose()


@respx.mock
async def test_fetch_events_raises_upstream_error_after_exhausting_retries(
    client: EonetClient,
) -> None:
    respx.get(f"{BASE_URL}/events").mock(return_value=httpx.Response(503))

    with pytest.raises(UpstreamServiceError):
        await client.fetch_events()

    await client.aclose()


@respx.mock
async def test_fetch_events_does_not_retry_on_client_error(client: EonetClient) -> None:
    route = respx.get(f"{BASE_URL}/events").mock(return_value=httpx.Response(404))

    with pytest.raises(UpstreamServiceError):
        await client.fetch_events()

    assert route.call_count == 1
    await client.aclose()


@respx.mock
async def test_fetch_events_passes_days_filter(client: EonetClient) -> None:
    route = respx.get(f"{BASE_URL}/events").mock(
        return_value=httpx.Response(200, json={"title": "EONET Events", "events": []})
    )

    await client.fetch_events(days=7)

    assert route.calls.last.request.url.params["days"] == "7"
    await client.aclose()


@respx.mock
async def test_fetch_events_retries_on_transport_error(client: EonetClient) -> None:
    route = respx.get(f"{BASE_URL}/events")
    route.side_effect = [
        httpx.ConnectError("connection refused"),
        httpx.Response(200, json={"title": "EONET Events", "events": []}),
    ]

    payload = await client.fetch_events()

    assert payload["title"] == "EONET Events"
    assert route.call_count == 2
    await client.aclose()


async def test_client_as_async_context_manager_closes_on_exit() -> None:
    async with EonetClient(base_url=BASE_URL, timeout_seconds=5.0, max_retries=3) as ctx_client:
        assert isinstance(ctx_client, EonetClient)
