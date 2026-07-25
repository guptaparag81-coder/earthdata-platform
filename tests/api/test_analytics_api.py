"""API tests for the analytics (summary/timeseries/export) endpoints."""

from httpx import AsyncClient

RAW_BASE = "/api/v1/raw-observations"
PROCESSED_BASE = "/api/v1/processed-observations"
ANALYTICS_BASE = "/api/v1/analytics"


async def _seed(client: AsyncClient) -> None:
    fixtures = [
        ("W1", "Wildfires", "eonet", True),
        ("W2", "Wildfires", "eonet", False),
        ("S1", "Severe Storms", "other", True),
    ]
    for external_id, category, source, is_open in fixtures:
        raw = (
            await client.post(
                RAW_BASE,
                json={
                    "source": source,
                    "external_id": external_id,
                    "payload": {"id": external_id},
                    "fetched_at": "2026-01-01T00:00:00Z",
                },
            )
        ).json()
        await client.post(
            PROCESSED_BASE,
            json={
                "raw_observation_id": raw["id"],
                "external_id": external_id,
                "title": f"Event {external_id}",
                "category": category,
                "source": source,
                "event_date": "2026-01-01T00:00:00Z",
                "latitude": 10.0,
                "longitude": 20.0,
                "is_open": is_open,
            },
        )


async def test_get_summary(db_client: AsyncClient) -> None:
    await _seed(db_client)

    response = await db_client.get(f"{ANALYTICS_BASE}/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["total_count"] == 3
    assert body["open_count"] == 2
    assert body["closed_count"] == 1


async def test_get_timeseries(db_client: AsyncClient) -> None:
    await _seed(db_client)

    response = await db_client.get(f"{ANALYTICS_BASE}/timeseries", params={"interval": "day"})

    assert response.status_code == 200
    body = response.json()
    assert body["interval"] == "day"
    assert sum(point["count"] for point in body["points"]) == 3


async def test_export_as_json(db_client: AsyncClient) -> None:
    await _seed(db_client)

    response = await db_client.get(
        f"{ANALYTICS_BASE}/export", params={"format": "json", "category": "Wildfires"}
    )

    assert response.status_code == 200
    body = response.json()
    assert {row["external_id"] for row in body} == {"W1", "W2"}


async def test_export_as_csv(db_client: AsyncClient) -> None:
    await _seed(db_client)

    response = await db_client.get(f"{ANALYTICS_BASE}/export", params={"format": "csv"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]
    lines = response.text.strip().splitlines()
    assert len(lines) == 4
