from typing import Any, Dict
import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, verify_internal_or_user
from app.schemas.reservation import (
    ConfirmReservationRequest,
    ConfirmReservationResponse,
    ReleaseRequest,
    ReleaseResponse,
    ReservationRequest,
    ReservationResponse,
)
from app.services.inventory_service import InventoryService

router = APIRouter(prefix="/events/{id}", tags=["Internal (ms-orders)"])


@router.post(
    "/reserve",
    response_model=ReservationResponse,
    status_code=status.HTTP_200_OK,
    summary="Reserva atómica de cupos por ms-orders",
)
async def reserve_spots(
    id: uuid.UUID,
    reservation_in: ReservationRequest,
    auth_data: Dict[str, Any] = Depends(verify_internal_or_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Bloquea atómicamente el sector mediante SELECT ... FOR UPDATE,
    descuenta cupos disponibles y genera la reserva con vencimiento de 10 min.
    Retorna 200 con importes calculados, 409 si cupos agotados o 404 si no existe.
    """
    return await InventoryService.reserve_spots(
        db,
        event_id=id,
        order_id=reservation_in.order_id,
        sector_id=reservation_in.sector_id,
        quantity=reservation_in.quantity,
    )


@router.post(
    "/release",
    response_model=ReleaseResponse,
    status_code=status.HTTP_200_OK,
    summary="Liberación compensatoria de cupos por ms-orders",
)
async def release_spots(
    id: uuid.UUID,
    release_in: ReleaseRequest,
    auth_data: Dict[str, Any] = Depends(verify_internal_or_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Transacción compensatoria invocada si el pago falla o expira.
    Repone los cupos al sector y cambia el estado de reserva a RELEASED.
    """
    return await InventoryService.release_spots(
        db,
        event_id=id,
        order_id=release_in.order_id,
    )


@router.post(
    "/confirm-reservation",
    response_model=ConfirmReservationResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirmación de reserva tras pago exitoso",
)
async def confirm_reservation(
    id: uuid.UUID,
    confirm_in: ConfirmReservationRequest,
    auth_data: Dict[str, Any] = Depends(verify_internal_or_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Marca la reserva como CONFIRMED tras aprobación de pago en ms-orders.
    """
    return await InventoryService.confirm_reservation(
        db,
        event_id=id,
        order_id=confirm_in.order_id,
    )
