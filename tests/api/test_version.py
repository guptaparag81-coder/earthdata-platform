"""Tests for the version endpoint."""

from httpx import AsyncClient

from earthdata import __version__


async def test_version_returns_app_metadata(client: AsyncClient) -> None:
    response = await client.get("/api/v1/version")

    assert response.status_code == 200
    body = response.json()
    assert body["app_name"] == "EarthData"
    assert body["environment"] == "test"
    assert body["version"] == __version__
