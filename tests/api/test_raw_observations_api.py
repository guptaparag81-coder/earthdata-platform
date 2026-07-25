"""API tests for raw observation CRUD endpoints."""

import uuid
from typing import Any

from httpx import AsyncClient

BASE = "/api/v1/raw-observations"


def _payload(external_id: str = "EONET_001", source: str = "eonet") -> dict[str, Any]:
    return {
        "source": source,
        "external_id": external_id,
        "payload": {"id": external_id, "title": "Test event"},
        "fetched_at": "2026-01-01T00:00:00Z",
    }


async def test_create_and_get_raw_observation(db_client: AsyncClient) -> None:
    create_response = await db_client.post(BASE, json=_payload())
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["external_id"] == "EONET_001"
    assert created["payload"]["title"] == "Test event"

    get_response = await db_client.get(f"{BASE}/{created['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == created["id"]


async def test_get_raw_observation_not_found(db_client: AsyncClient) -> None:
    response = await db_client.get(f"{BASE}/{uuid.uuid4()}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "record_not_found"


async def test_create_raw_observation_validation_error(db_client: AsyncClient) -> None:
    response = await db_client.post(BASE, json={"source": "", "external_id": ""})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "request_validation_error"


async def test_delete_raw_observation(db_client: AsyncClient) -> None:
    created = (await db_client.post(BASE, json=_payload())).json()

    delete_response = await db_client.delete(f"{BASE}/{created['id']}")
    assert delete_response.status_code == 204

    get_response = await db_client.get(f"{BASE}/{created['id']}")
    assert get_response.status_code == 404


async def test_delete_raw_observation_not_found(db_client: AsyncClient) -> None:
    response = await db_client.delete(f"{BASE}/{uuid.uuid4()}")

    assert response.status_code == 404


async def test_list_raw_observations_pagination_filtering_sorting(
    db_client: AsyncClient,
) -> None:
    for i in range(3):
        await db_client.post(BASE, json=_payload(external_id=f"EONET_{i}"))
    await db_client.post(BASE, json=_payload(external_id="OTHER_1", source="other"))

    page_response = await db_client.get(BASE, params={"limit": 2, "offset": 0})
    assert page_response.status_code == 200
    page = page_response.json()
    assert page["total"] == 4
    assert page["limit"] == 2
    assert page["offset"] == 0
    assert len(page["items"]) == 2
    assert page["has_more"] is True

    filtered_response = await db_client.get(BASE, params={"source": "other"})
    filtered = filtered_response.json()
    assert filtered["total"] == 1
    assert filtered["items"][0]["external_id"] == "OTHER_1"

    sorted_response = await db_client.get(
        BASE, params={"sort_by": "external_id", "sort_order": "asc", "source": "eonet"}
    )
    sorted_items = sorted_response.json()["items"]
    assert [item["external_id"] for item in sorted_items] == ["EONET_0", "EONET_1", "EONET_2"]
