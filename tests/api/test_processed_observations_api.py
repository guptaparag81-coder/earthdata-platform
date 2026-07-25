"""API tests for processed observation CRUD endpoints."""

import uuid
from typing import Any

from httpx import AsyncClient

RAW_BASE = "/api/v1/raw-observations"
BASE = "/api/v1/processed-observations"


async def _create_raw(client: AsyncClient, external_id: str) -> str:
    payload = {
        "source": "eonet",
        "external_id": external_id,
        "payload": {"id": external_id},
        "fetched_at": "2026-01-01T00:00:00Z",
    }
    response = await client.post(RAW_BASE, json=payload)
    result: str = response.json()["id"]
    return result


def _processed_payload(
    raw_id: str,
    external_id: str = "EONET_001",
    category: str = "Wildfires",
    source: str = "eonet",
    is_open: bool = True,
) -> dict[str, Any]:
    return {
        "raw_observation_id": raw_id,
        "external_id": external_id,
        "title": f"Event {external_id}",
        "category": category,
        "source": source,
        "event_date": "2026-01-01T00:00:00Z",
        "latitude": 10.0,
        "longitude": 20.0,
        "is_open": is_open,
    }


async def test_create_and_get_processed_observation(db_client: AsyncClient) -> None:
    raw_id = await _create_raw(db_client, "EONET_001")

    create_response = await db_client.post(BASE, json=_processed_payload(raw_id))
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["category"] == "Wildfires"

    get_response = await db_client.get(f"{BASE}/{created['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["external_id"] == "EONET_001"


async def test_get_processed_observation_not_found(db_client: AsyncClient) -> None:
    response = await db_client.get(f"{BASE}/{uuid.uuid4()}")
    assert response.status_code == 404


async def test_create_processed_observation_validation_error(db_client: AsyncClient) -> None:
    response = await db_client.post(
        BASE,
        json={
            "raw_observation_id": str(uuid.uuid4()),
            "external_id": "X",
            "title": "T",
            "category": "C",
            "source": "eonet",
            "event_date": "2026-01-01T00:00:00Z",
            "latitude": 200.0,
            "longitude": 20.0,
        },
    )

    assert response.status_code == 422


async def test_update_processed_observation(db_client: AsyncClient) -> None:
    raw_id = await _create_raw(db_client, "EONET_002")
    created = (await db_client.post(BASE, json=_processed_payload(raw_id, "EONET_002"))).json()

    patch_response = await db_client.patch(
        f"{BASE}/{created['id']}", json={"is_open": False, "title": "Updated title"}
    )

    assert patch_response.status_code == 200
    updated = patch_response.json()
    assert updated["is_open"] is False
    assert updated["title"] == "Updated title"
    assert updated["category"] == "Wildfires"


async def test_update_processed_observation_not_found(db_client: AsyncClient) -> None:
    response = await db_client.patch(f"{BASE}/{uuid.uuid4()}", json={"is_open": False})
    assert response.status_code == 404


async def test_delete_processed_observation(db_client: AsyncClient) -> None:
    raw_id = await _create_raw(db_client, "EONET_003")
    created = (await db_client.post(BASE, json=_processed_payload(raw_id, "EONET_003"))).json()

    delete_response = await db_client.delete(f"{BASE}/{created['id']}")
    assert delete_response.status_code == 204

    assert (await db_client.get(f"{BASE}/{created['id']}")).status_code == 404


async def test_delete_processed_observation_not_found(db_client: AsyncClient) -> None:
    response = await db_client.delete(f"{BASE}/{uuid.uuid4()}")
    assert response.status_code == 404


async def test_list_processed_observations_pagination_filtering_sorting(
    db_client: AsyncClient,
) -> None:
    raw_1 = await _create_raw(db_client, "EONET_A")
    raw_2 = await _create_raw(db_client, "EONET_B")
    raw_3 = await _create_raw(db_client, "EONET_C")

    await db_client.post(
        BASE, json=_processed_payload(raw_1, "EONET_A", category="Wildfires", is_open=True)
    )
    await db_client.post(
        BASE, json=_processed_payload(raw_2, "EONET_B", category="Wildfires", is_open=False)
    )
    await db_client.post(
        BASE,
        json=_processed_payload(raw_3, "EONET_C", category="Severe Storms", source="other"),
    )

    page_response = await db_client.get(BASE, params={"limit": 2})
    page = page_response.json()
    assert page["total"] == 3
    assert len(page["items"]) == 2

    category_response = await db_client.get(BASE, params={"category": "Wildfires"})
    category_items = category_response.json()["items"]
    assert {item["external_id"] for item in category_items} == {"EONET_A", "EONET_B"}

    open_response = await db_client.get(BASE, params={"is_open": "true"})
    open_items = open_response.json()["items"]
    assert {item["external_id"] for item in open_items} == {"EONET_A", "EONET_C"}

    sorted_response = await db_client.get(
        BASE, params={"sort_by": "external_id", "sort_order": "asc"}
    )
    sorted_items = sorted_response.json()["items"]
    assert [item["external_id"] for item in sorted_items] == ["EONET_A", "EONET_B", "EONET_C"]
