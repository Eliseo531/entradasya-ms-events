from datetime import datetime, timedelta, timezone
from decimal import Decimal
import uuid
import pytest
from httpx import AsyncClient

from app.models.event import Event


@pytest.mark.asyncio
async def test_create_event_success(client: AsyncClient, organizer_headers: dict):
    payload = {
        "title": "Concierto Electrónico 2026",
        "description": "El evento de música electrónica más esperado",
        "venue": "Explanada del Parque",
        "event_date": (datetime.now(timezone.utc) + timedelta(days=45)).isoformat(),
        "image_url": "https://images.unsplash.com/photo-electro",
        "sectors": [
            {"name": "General", "capacity": 500, "price": 80.00},
            {"name": "VIP", "capacity": 150, "price": 200.00},
        ],
    }

    response = await client.post("/api/v1/events", json=payload, headers=organizer_headers)
    assert response.status_code == 201
    data = response.json()

    assert data["title"] == "Concierto Electrónico 2026"
    assert data["status"] == "DRAFT"
    assert len(data["sectors"]) == 2

    # Check sectors initialized with available_spots == capacity
    sec_gen = next(s for s in data["sectors"] if s["name"] == "General")
    assert sec_gen["capacity"] == 500
    assert sec_gen["available_spots"] == 500
    assert Decimal(str(sec_gen["price"])) == Decimal("80.00")


@pytest.mark.asyncio
async def test_create_event_forbidden_for_client(
    client: AsyncClient, client_headers: dict
):
    payload = {
        "title": "Intento no autorizado",
        "venue": "Cualquiera",
        "event_date": (datetime.now(timezone.utc) + timedelta(days=10)).isoformat(),
        "sectors": [{"name": "General", "capacity": 100, "price": 50.00}],
    }
    response = await client.post("/api/v1/events", json=payload, headers=client_headers)
    assert response.status_code == 403
    assert "requiere rol de organizador" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_event_unauthorized_without_token(client: AsyncClient):
    payload = {
        "title": "Sin token",
        "venue": "Cualquiera",
        "event_date": (datetime.now(timezone.utc) + timedelta(days=10)).isoformat(),
        "sectors": [{"name": "General", "capacity": 100, "price": 50.00}],
    }
    response = await client.post("/api/v1/events", json=payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_event_by_owner(
    client: AsyncClient,
    organizer_headers: dict,
    sample_published_event: Event,
):
    event_id = sample_published_event.id
    update_payload = {
        "title": "Concierto de Rock Nacional - Edición Especial",
        "venue": "Estadio Hernando Siles",
    }
    response = await client.put(
        f"/api/v1/events/{event_id}",
        json=update_payload,
        headers=organizer_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Concierto de Rock Nacional - Edición Especial"
    assert data["venue"] == "Estadio Hernando Siles"


@pytest.mark.asyncio
async def test_update_event_forbidden_for_other_organizer(
    client: AsyncClient,
    other_organizer_headers: dict,
    sample_published_event: Event,
):
    event_id = sample_published_event.id
    update_payload = {"title": "Intento de usurpación"}
    response = await client.put(
        f"/api/v1/events/{event_id}",
        json=update_payload,
        headers=other_organizer_headers,
    )
    assert response.status_code == 403
    assert "No tienes permiso para modificar este evento" in response.json()["detail"]


@pytest.mark.asyncio
async def test_update_event_status_publish_and_cancel(
    client: AsyncClient,
    organizer_headers: dict,
):
    # First create in DRAFT
    create_payload = {
        "title": "Obra de Teatro",
        "venue": "Teatro Municipal",
        "event_date": (datetime.now(timezone.utc) + timedelta(days=15)).isoformat(),
        "sectors": [{"name": "Platea", "capacity": 80, "price": 60.00}],
    }
    res_create = await client.post(
        "/api/v1/events", json=create_payload, headers=organizer_headers
    )
    assert res_create.status_code == 201
    event_id = res_create.json()["id"]

    # Publish
    res_pub = await client.patch(
        f"/api/v1/events/{event_id}/status",
        json={"status": "PUBLISHED"},
        headers=organizer_headers,
    )
    assert res_pub.status_code == 200
    assert res_pub.json()["status"] == "PUBLISHED"

    # Cancel
    res_cancel = await client.patch(
        f"/api/v1/events/{event_id}/status",
        json={"status": "CANCELLED"},
        headers=organizer_headers,
    )
    assert res_cancel.status_code == 200
    assert res_cancel.json()["status"] == "CANCELLED"


@pytest.mark.asyncio
async def test_list_organizer_events(
    client: AsyncClient,
    organizer_headers: dict,
    sample_published_event: Event,
):
    response = await client.get("/api/v1/organizer/events", headers=organizer_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(ev["id"] == str(sample_published_event.id) for ev in data)
