from decimal import Decimal
import uuid
import pytest
from httpx import AsyncClient

from app.models.event import Event


@pytest.mark.asyncio
async def test_atomic_reservation_success(
    client: AsyncClient,
    sample_published_event: Event,
    internal_headers: dict,
):
    event_id = sample_published_event.id
    vip_sector = next(s for s in sample_published_event.sectors if s.name == "VIP")
    sector_id = vip_sector.id
    initial_spots = vip_sector.available_spots  # 100

    order_id = uuid.uuid4()
    quantity = 2

    reserve_payload = {
        "order_id": str(order_id),
        "sector_id": str(sector_id),
        "quantity": quantity,
    }

    response = await client.post(
        f"/api/v1/events/{event_id}/reserve",
        json=reserve_payload,
        headers=internal_headers,
    )
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "RESERVED"
    assert data["order_id"] == str(order_id)
    assert data["event_id"] == str(event_id)
    assert data["sector_id"] == str(sector_id)
    assert data["quantity"] == 2
    assert Decimal(str(data["unit_price"])) == Decimal("200.00")
    assert Decimal(str(data["total_amount"])) == Decimal("400.00")
    assert "expires_at" in data

    # Verify event detail reflects decremented spots
    detail_res = await client.get(f"/api/v1/events/{event_id}")
    detail_vip = next(s for s in detail_res.json()["sectors"] if s["id"] == str(sector_id))
    assert detail_vip["available_spots"] == initial_spots - quantity


@pytest.mark.asyncio
async def test_atomic_reservation_idempotency(
    client: AsyncClient,
    sample_published_event: Event,
    internal_headers: dict,
):
    event_id = sample_published_event.id
    vip_sector = next(s for s in sample_published_event.sectors if s.name == "VIP")
    sector_id = vip_sector.id
    order_id = uuid.uuid4()

    reserve_payload = {
        "order_id": str(order_id),
        "sector_id": str(sector_id),
        "quantity": 2,
    }

    # First call
    res1 = await client.post(
        f"/api/v1/events/{event_id}/reserve",
        json=reserve_payload,
        headers=internal_headers,
    )
    assert res1.status_code == 200

    # Repeat call with identical order_id
    res2 = await client.post(
        f"/api/v1/events/{event_id}/reserve",
        json=reserve_payload,
        headers=internal_headers,
    )
    assert res2.status_code == 200
    assert res2.json()["order_id"] == str(order_id)

    # Check available spots were only decremented once (100 - 2 = 98)
    detail_res = await client.get(f"/api/v1/events/{event_id}")
    detail_vip = next(s for s in detail_res.json()["sectors"] if s["id"] == str(sector_id))
    assert detail_vip["available_spots"] == 98


@pytest.mark.asyncio
async def test_reservation_out_of_stock_409(
    client: AsyncClient,
    sample_published_event: Event,
    internal_headers: dict,
):
    event_id = sample_published_event.id
    vip_sector = next(s for s in sample_published_event.sectors if s.name == "VIP")
    sector_id = vip_sector.id

    # Reserve almost all spots first
    vip_sector.available_spots = 1

    order_id = uuid.uuid4()
    # Request 2 spots when only 1 is available
    reserve_payload = {
        "order_id": str(order_id),
        "sector_id": str(sector_id),
        "quantity": 2,
    }

    response = await client.post(
        f"/api/v1/events/{event_id}/reserve",
        json=reserve_payload,
        headers=internal_headers,
    )
    assert response.status_code == 409
    data = response.json()
    assert data["code"] == "EVENTS_OUT_OF_STOCK"
    assert data["message"] == "Cupos insuficientes en el sector seleccionado"
    assert data["available_spots"] == 1


@pytest.mark.asyncio
async def test_reservation_not_found_404(
    client: AsyncClient,
    sample_published_event: Event,
    internal_headers: dict,
):
    event_id = sample_published_event.id
    random_sector_id = uuid.uuid4()

    reserve_payload = {
        "order_id": str(uuid.uuid4()),
        "sector_id": str(random_sector_id),
        "quantity": 1,
    }

    response = await client.post(
        f"/api/v1/events/{event_id}/reserve",
        json=reserve_payload,
        headers=internal_headers,
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "EVENTS_NOT_FOUND"


@pytest.mark.asyncio
async def test_compensatory_release_and_restoration_of_spots(
    client: AsyncClient,
    sample_published_event: Event,
    internal_headers: dict,
):
    event_id = sample_published_event.id
    gen_sector = next(s for s in sample_published_event.sectors if s.name == "General")
    sector_id = gen_sector.id
    initial_spots = gen_sector.available_spots  # 300

    order_id = uuid.uuid4()
    quantity = 4

    # 1. Reserve 4 spots
    reserve_res = await client.post(
        f"/api/v1/events/{event_id}/reserve",
        json={"order_id": str(order_id), "sector_id": str(sector_id), "quantity": quantity},
        headers=internal_headers,
    )
    assert reserve_res.status_code == 200

    # Verify spots decremented to 296
    detail1 = await client.get(f"/api/v1/events/{event_id}")
    sec1 = next(s for s in detail1.json()["sectors"] if s["id"] == str(sector_id))
    assert sec1["available_spots"] == initial_spots - quantity

    # 2. Release spots (simulating failed payment)
    release_res = await client.post(
        f"/api/v1/events/{event_id}/release",
        json={"order_id": str(order_id)},
        headers=internal_headers,
    )
    assert release_res.status_code == 200
    data_release = release_res.json()
    assert data_release["status"] == "RELEASED"
    assert data_release["order_id"] == str(order_id)
    assert data_release["message"] == "Cupos liberados exitosamente"

    # Verify spots restored back to initial_spots (300)
    detail2 = await client.get(f"/api/v1/events/{event_id}")
    sec2 = next(s for s in detail2.json()["sectors"] if s["id"] == str(sector_id))
    assert sec2["available_spots"] == initial_spots

    # 3. Idempotent release call
    release_res2 = await client.post(
        f"/api/v1/events/{event_id}/release",
        json={"order_id": str(order_id)},
        headers=internal_headers,
    )
    assert release_res2.status_code == 200

    # Ensure spots did not over-increment
    detail3 = await client.get(f"/api/v1/events/{event_id}")
    sec3 = next(s for s in detail3.json()["sectors"] if s["id"] == str(sector_id))
    assert sec3["available_spots"] == initial_spots


@pytest.mark.asyncio
async def test_confirm_reservation_success(
    client: AsyncClient,
    sample_published_event: Event,
    internal_headers: dict,
):
    event_id = sample_published_event.id
    vip_sector = next(s for s in sample_published_event.sectors if s.name == "VIP")
    sector_id = vip_sector.id
    order_id = uuid.uuid4()

    # 1. Reserve
    await client.post(
        f"/api/v1/events/{event_id}/reserve",
        json={"order_id": str(order_id), "sector_id": str(sector_id), "quantity": 1},
        headers=internal_headers,
    )

    # 2. Confirm
    confirm_res = await client.post(
        f"/api/v1/events/{event_id}/confirm-reservation",
        json={"order_id": str(order_id)},
        headers=internal_headers,
    )
    assert confirm_res.status_code == 200
    assert confirm_res.json()["status"] == "CONFIRMED"

    # 3. Cannot release confirmed reservation
    release_res = await client.post(
        f"/api/v1/events/{event_id}/release",
        json={"order_id": str(order_id)},
        headers=internal_headers,
    )
    assert release_res.status_code == 409


@pytest.mark.asyncio
async def test_reserve_with_client_jwt(
    client: AsyncClient,
    sample_published_event: Event,
    client_headers: dict,
):
    event_id = sample_published_event.id
    vip_sector = next(s for s in sample_published_event.sectors if s.name == "VIP")
    sector_id = vip_sector.id
    order_id = uuid.uuid4()

    # Client Bearer token should be accepted on /reserve according to contract
    response = await client.post(
        f"/api/v1/events/{event_id}/reserve",
        json={"order_id": str(order_id), "sector_id": str(sector_id), "quantity": 1},
        headers=client_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "RESERVED"


@pytest.mark.asyncio
async def test_reserve_unauthorized_without_headers(
    client: AsyncClient,
    sample_published_event: Event,
):
    event_id = sample_published_event.id
    vip_sector = next(s for s in sample_published_event.sectors if s.name == "VIP")
    sector_id = vip_sector.id

    response = await client.post(
        f"/api/v1/events/{event_id}/reserve",
        json={"order_id": str(uuid.uuid4()), "sector_id": str(sector_id), "quantity": 1},
    )
    assert response.status_code == 401
