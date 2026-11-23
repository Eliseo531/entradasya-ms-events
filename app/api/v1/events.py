from typing import Optional
import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.schemas.event import EventPublicListResponse, EventResponse
from app.services.event_service import EventService

router = APIRouter(prefix="/events", tags=["Events"])


@router.get(
    "",
    response_model=EventPublicListResponse,
    summary="Cartelera pública de eventos publicados",
)
async def list_public_events(
    search: Optional[str] = Query(None, description="Búsqueda por título, lugar o descripción"),
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(10, ge=1, le=100, description="Cantidad de eventos por página"),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista eventos con estado PUBLISHED y fecha futura.
    Permite búsqueda por texto y paginación.
    """
    return await EventService.get_public_events(db, search=search, page=page, limit=limit)


@router.get(
    "/{id}",
    response_model=EventResponse,
    summary="Detalle completo de un evento con sus sectores",
)
async def get_event_detail(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna la información completa del evento junto a la lista de sectores,
    sus precios y cupos disponibles.
    """
    return await EventService.get_event_by_id(db, id)
