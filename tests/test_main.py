"""Tests for application startup/shutdown (lifespan) and app factory."""

from starlette.testclient import TestClient

from earthdata.main import create_app


def test_lifespan_runs_startup_and_shutdown() -> None:
    app = create_app()

    with TestClient(app) as test_client:
        response = test_client.get("/api/v1/version")
        assert response.status_code == 200
