import asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import AsyncGenerator
import uuid
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.api.dependencies import get_db
from app.core.config import settings
from app.core.security import create_access_token
from app.main import app
from app.models.base import Base
from app.models.event import Event
from app.models.sector import Sector


# Test database setup (in-memory SQLite with StaticPool)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    """Creates database schema before each test and drops it after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provides a transactional database session for tests."""
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """HTTP async client configured with dependency overrides."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()


# Pre-defined test identities
ORGANIZER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
OTHER_ORGANIZER_ID = uuid.UUID("99999999-9999-9999-9999-999999999999")
CLIENT_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")


@pytest.fixture
def organizer_headers():
    token = create_access_token(
        {
            "sub": str(ORGANIZER_ID),
            "name": "Organizador Principal",
            "email": "organizador@entradasya.com",
            "role": "organizador",
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def other_organizer_headers():
    token = create_access_token(
        {
            "sub": str(OTHER_ORGANIZER_ID),
            "name": "Otro Organizador",
            "email": "otro@entradasya.com",
            "role": "organizador",
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client_headers():
    token = create_access_token(
        {
            "sub": str(CLIENT_ID),
            "name": "Cliente Frecuente",
            "email": "cliente@entradasya.com",
            "role": "cliente",
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def internal_headers():
    return {"X-Internal-Token": settings.INTERNAL_TOKEN}


@pytest_asyncio.fixture
async def sample_published_event(db_session: AsyncSession) -> Event:
    """Creates a sample published event with 2 sectors."""
    event = Event(
        id=uuid.UUID("b1a2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d"),
        organizer_id=ORGANIZER_ID,
        title="Concierto de Rock Nacional",
        description="Gran concierto de rock",
        venue="Teatro al Aire Libre",
        event_date=datetime.now(timezone.utc) + timedelta(days=30),
        image_url="https://images.unsplash.com/photo-1470225620780-dba8ba36b745",
        status="PUBLISHED",
    )
    sector_vip = Sector(
        id=uuid.UUID("3f2e1d0c-4b5a-6a7b-8c9d-0e1f2a3b4c5d"),
        name="VIP",
        capacity=100,
        available_spots=100,
        price=Decimal("200.00"),
    )
    sector_gen = Sector(
        id=uuid.UUID("4f2e1d0c-4b5a-6a7b-8c9d-0e1f2a3b4c5e"),
        name="General",
        capacity=300,
        available_spots=300,
        price=Decimal("80.00"),
    )
    event.sectors.append(sector_vip)
    event.sectors.append(sector_gen)

    db_session.add(event)
    await db_session.commit()
    await db_session.refresh(event)
    return event
