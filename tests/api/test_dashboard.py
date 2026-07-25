"""Tests for the interactive HTML dashboard endpoint."""

from httpx import AsyncClient


async def test_dashboard_returns_html_page(client: AsyncClient) -> None:
    response = await client.get("/api/v1/dashboard")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "EarthData Dashboard" in response.text
    assert "chart.js" in response.text
