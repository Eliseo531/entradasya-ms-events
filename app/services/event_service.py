from datetime import datetime, timezone
from typing import List, Optional
import uuid
from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.event import Event
from app.models.sector import Sector
from app.schemas.event import (
    EventCreate,
    EventPublicItem,
    EventPublicListResponse,
    EventUpdate,
)
from app.schemas.sector import SectorPublicResponse


class EventService:
    @staticmethod
    async def get_public_events(
        db: AsyncSession,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 10,
    ) -> EventPublicListResponse:
        now = datetime.now(timezone.utc)
        
        # Base query filters
        filters = [
            Event.status == "PUBLISHED",
            Event.event_date >= now,
        ]

        if search and search.strip():
            term = f"%{search.strip()}%"
            filters.append(
                or_(
                    Event.title.ilike(term),
                    Event.venue.ilike(term),
                    Event.description.ilike(term),
                )
            )

        # Count total matching events
        count_stmt = select(func.count(Event.id)).where(*filters)
        count_res = await db.execute(count_stmt)
        total = count_res.scalar_one()

        # Query paginated events with sectors preloaded
        offset = max(0, (page - 1) * limit)
        stmt = (
            select(Event)
            .where(*filters)
            .options(selectinload(Event.sectors))
            .order_by(Event.event_date.asc())
            .offset(offset)
            .limit(limit)
        )
        res = await db.execute(stmt)
        events = res.scalars().all()

        # Build public items with min_price
        public_items: List[EventPublicItem] = []
        for ev in events:
            min_price = min((s.price for s in ev.sectors), default=None)
            public_sectors = [
                SectorPublicResponse(
                    id=s.id,
                    name=s.name,
                    capacity=s.capacity,
                    available_spots=s.available_spots,
                    price=s.price,
                )
                for s in ev.sectors
            ]
            public_items.append(
                EventPublicItem(
                    id=ev.id,
                    title=ev.title,
                    description=ev.description,
                    venue=ev.venue,
                    event_date=ev.event_date,
                    image_url=ev.image_url,
                    status=ev.status,
                    min_price=min_price,
                    sectors=public_sectors,
                )
            )

        total_pages = (total + limit - 1) // limit if total > 0 else 1

        return EventPublicListResponse(
            events=public_items,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
        )

    @staticmethod
    async def get_event_by_id(db: AsyncSession, event_id: uuid.UUID) -> Event:
        stmt = (
            select(Event)
            .where(Event.id == event_id)
            .options(selectinload(Event.sectors))
        )
        res = await db.execute(stmt)
        event = res.scalar_one_or_none()
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evento no encontrado",
            )
        return event

    @staticmethod
    async def create_event(
        db: AsyncSession,
        organizer_id: uuid.UUID,
        event_in: EventCreate,
    ) -> Event:
        event = Event(
            organizer_id=organizer_id,
            title=event_in.title,
            description=event_in.description,
            venue=event_in.venue,
            event_date=event_in.event_date,
            image_url=event_in.image_url,
            status="DRAFT",
        )

        for sector_data in event_in.sectors:
            sector = Sector(
                name=sector_data.name,
                capacity=sector_data.capacity,
                available_spots=sector_data.capacity,
                price=sector_data.price,
            )
            event.sectors.append(sector)

        db.add(event)
        await db.commit()
        await db.refresh(event)

        # Ensure sectors are fully loaded
        return await EventService.get_event_by_id(db, event.id)

    @staticmethod
    async def update_event(
        db: AsyncSession,
        event_id: uuid.UUID,
        organizer_id: uuid.UUID,
        event_in: EventUpdate,
    ) -> Event:
        event = await EventService.get_event_by_id(db, event_id)

        if event.organizer_id != organizer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para modificar este evento",
            )

        update_data = event_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(event, key, value)

        await db.commit()
        await db.refresh(event)
        return await EventService.get_event_by_id(db, event.id)

    @staticmethod
    async def update_event_status(
        db: AsyncSession,
        event_id: uuid.UUID,
        organizer_id: uuid.UUID,
        new_status: str,
    ) -> Event:
        event = await EventService.get_event_by_id(db, event_id)

        if event.organizer_id != organizer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para modificar este evento",
            )

        event.status = new_status
        await db.commit()
        await db.refresh(event)
        return await EventService.get_event_by_id(db, event.id)

    @staticmethod
    async def get_organizer_events(
        db: AsyncSession,
        organizer_id: uuid.UUID,
    ) -> List[Event]:
        stmt = (
            select(Event)
            .where(Event.organizer_id == organizer_id)
            .options(selectinload(Event.sectors))
            .order_by(Event.created_at.desc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())
