from typing import Any, Dict, List
import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, require_organizer
from app.schemas.event import (
    EventCreate,
    EventResponse,
    EventStatusUpdate,
    EventUpdate,
)
from app.services.event_service import EventService

router = APIRouter(tags=["Organizer"])


@router.get(
    "/organizer/events",
    response_model=List[EventResponse],
    summary="Lista de eventos creados por el organizador autenticado",
)
async def list_organizer_events(
    organizer: Dict[str, Any] = Depends(require_organizer),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna todos los eventos (DRAFT, PUBLISHED, CANCELLED) creados
    por el organizador autenticado.
    """
    return await EventService.get_organizer_events(db, organizer_id=organizer["id"])


@router.post(
    "/events",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nuevo evento con sectores en estado DRAFT",
)
async def create_event(
    event_in: EventCreate,
    organizer: Dict[str, Any] = Depends(require_organizer),
    db: AsyncSession = Depends(get_db),
):
    """
    Crea un evento nuevo en estado DRAFT junto a sus sectores y capacidades.
    Solo accesible para usuarios con rol 'organizador'.
    """
    return await EventService.create_event(
        db, organizer_id=organizer["id"], event_in=event_in
    )


@router.put(
    "/events/{id}",
    response_model=EventResponse,
    summary="Editar información de un evento existente",
)
async def update_event(
    id: uuid.UUID,
    event_in: EventUpdate,
    organizer: Dict[str, Any] = Depends(require_organizer),
    db: AsyncSession = Depends(get_db),
):
    """
    Actualiza datos generales del evento (título, descripción, fecha, recinto).
    Requiere ser el organizador propietario del evento.
    """
    return await EventService.update_event(
        db, event_id=id, organizer_id=organizer["id"], event_in=event_in
    )


@router.patch(
    "/events/{id}/status",
    response_model=EventResponse,
    summary="Cambiar estado del evento a PUBLISHED o CANCELLED",
)
async def update_event_status(
    id: uuid.UUID,
    status_in: EventStatusUpdate,
    organizer: Dict[str, Any] = Depends(require_organizer),
    db: AsyncSession = Depends(get_db),
):
    """
    Cambia el estado del evento (ej. de DRAFT a PUBLISHED, o a CANCELLED).
    Requiere ser el organizador propietario del evento.
    """
    return await EventService.update_event_status(
        db, event_id=id, organizer_id=organizer["id"], new_status=status_in.status
    )
