from datetime import datetime, timedelta, timezone
from decimal import Decimal
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.models.sector import Sector


@pytest.mark.asyncio
async def test_list_public_events_returns_only_published_and_future(
    client: AsyncClient,
    db_session: AsyncSession,
    sample_published_event: Event,
):
    now = datetime.now(timezone.utc)
    organizer_id = sample_published_event.organizer_id

    # Add a DRAFT event (should be excluded)
    draft_event = Event(
        organizer_id=organizer_id,
        title="Evento en Borrador",
        venue="Auditorio Secreto",
        event_date=now + timedelta(days=10),
        status="DRAFT",
    )
    # Add a PAST event (should be excluded)
    past_event = Event(
        organizer_id=organizer_id,
        title="Evento Ya Pasado",
        venue="Estadio",
        event_date=now - timedelta(days=10),
        status="PUBLISHED",
    )
    db_session.add_all([draft_event, past_event])
    await db_session.commit()

    response = await client.get("/api/v1/events")
    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 1
    assert len(data["events"]) == 1
    event_item = data["events"][0]
    assert event_item["id"] == str(sample_published_event.id)
    assert event_item["title"] == "Concierto de Rock Nacional"
    assert Decimal(str(event_item["min_price"])) == Decimal("80.00")
    assert len(event_item["sectors"]) == 2


@pytest.mark.asyncio
async def test_search_public_events(
    client: AsyncClient,
    db_session: AsyncSession,
    sample_published_event: Event,
):
    now = datetime.now(timezone.utc)
    organizer_id = sample_published_event.organizer_id

    # Another published event
    jazz_event = Event(
        organizer_id=organizer_id,
        title="Festival Internacional de Jazz",
        description="Fusión de jazz contemporáneo",
        venue="Centro Cultural Central",
        event_date=now + timedelta(days=20),
        status="PUBLISHED",
    )
    jazz_sector = Sector(
        name="Platea",
        capacity=100,
        available_spots=100,
        price=Decimal("120.00"),
    )
    jazz_event.sectors.append(jazz_sector)
    db_session.add(jazz_event)
    await db_session.commit()

    # Search for "Jazz"
    res_jazz = await client.get("/api/v1/events?search=Jazz")
    assert res_jazz.status_code == 200
    data_jazz = res_jazz.json()
    assert data_jazz["total"] == 1
    assert data_jazz["events"][0]["title"] == "Festival Internacional de Jazz"

    # Search for "Teatro" (venue search)
    res_venue = await client.get("/api/v1/events?search=Teatro")
    assert res_venue.status_code == 200
    data_venue = res_venue.json()
    assert data_venue["total"] == 1
    assert data_venue["events"][0]["title"] == "Concierto de Rock Nacional"

    # Search without results
    res_none = await client.get("/api/v1/events?search=Inexistente12345")
    assert res_none.status_code == 200
    assert res_none.json()["total"] == 0
    assert len(res_none.json()["events"]) == 0


@pytest.mark.asyncio
async def test_pagination_public_events(
    client: AsyncClient,
    db_session: AsyncSession,
    sample_published_event: Event,
):
    now = datetime.now(timezone.utc)
    organizer_id = sample_published_event.organizer_id

    # Add 2 more events
    for i in range(2):
        ev = Event(
            organizer_id=organizer_id,
            title=f"Evento Extra {i}",
            venue="Lugar",
            event_date=now + timedelta(days=i + 5),
            status="PUBLISHED",
        )
        db_session.add(ev)
    await db_session.commit()

    # Total 3 published events. Query limit 2, page 1
    res_p1 = await client.get("/api/v1/events?page=1&limit=2")
    assert res_p1.status_code == 200
    d1 = res_p1.json()
    assert d1["total"] == 3
    assert len(d1["events"]) == 2
    assert d1["total_pages"] == 2
    assert d1["page"] == 1

    # Page 2
    res_p2 = await client.get("/api/v1/events?page=2&limit=2")
    assert res_p2.status_code == 200
    d2 = res_p2.json()
    assert len(d2["events"]) == 1
    assert d2["page"] == 2


@pytest.mark.asyncio
async def test_get_event_detail_success(
    client: AsyncClient,
    sample_published_event: Event,
):
    event_id = sample_published_event.id
    response = await client.get(f"/api/v1/events/{event_id}")
    assert response.status_code == 200
    data = response.json()

    assert data["id"] == str(event_id)
    assert data["title"] == "Concierto de Rock Nacional"
    assert data["status"] == "PUBLISHED"
    assert len(data["sectors"]) == 2

    # Verify sector fields
    vip_sector = next(s for s in data["sectors"] if s["name"] == "VIP")
    assert vip_sector["capacity"] == 100
    assert vip_sector["available_spots"] == 100
    assert Decimal(str(vip_sector["price"])) == Decimal("200.00")


@pytest.mark.asyncio
async def test_get_event_detail_not_found(client: AsyncClient):
    random_id = uuid.uuid4()
    response = await client.get(f"/api/v1/events/{random_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Evento no encontrado"
