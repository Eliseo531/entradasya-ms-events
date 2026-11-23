import pytest
from httpx import AsyncClient
from unittest.mock import patch


@pytest.mark.asyncio
async def test_health_live_endpoint(client: AsyncClient):
    response = await client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "UP"
    assert data["service"] == "ms-events"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_health_ready_connected(client: AsyncClient):
    with patch("app.main.check_db_ready", return_value=True):
        response = await client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "UP"
        assert data["database"] == "connected"


@pytest.mark.asyncio
async def test_health_ready_disconnected(client: AsyncClient):
    with patch("app.main.check_db_ready", return_value=False):
        response = await client.get("/health/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "DOWN"
        assert data["database"] == "disconnected"


@pytest.mark.asyncio
async def test_legacy_health_endpoint(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "UP"
    assert data["service"] == "ms-events"
