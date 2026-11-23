from datetime import datetime, timedelta, timezone
from decimal import Decimal
import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.models.sector import Sector
from app.models.reservation import Reservation
from app.schemas.reservation import (
    ConfirmReservationResponse,
    ReleaseResponse,
    ReservationResponse,
)


class EventsNotFoundException(Exception):
    def __init__(self, message: str = "El evento o sector especificado no existe"):
        self.code = "EVENTS_NOT_FOUND"
        self.message = message
        super().__init__(self.message)


class OutOfStockException(Exception):
    def __init__(
        self,
        message: str = "Cupos insuficientes en el sector seleccionado",
        available_spots: int = 0,
    ):
        self.code = "EVENTS_OUT_OF_STOCK"
        self.message = message
        self.available_spots = available_spots
        super().__init__(self.message)


class ReservationConflictException(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(self.message)


class InventoryService:
    @staticmethod
    async def reserve_spots(
        db: AsyncSession,
        event_id: uuid.UUID,
        order_id: uuid.UUID,
        sector_id: uuid.UUID,
        quantity: int,
    ) -> ReservationResponse:
        # Check if reservation for this order already exists (idempotency check)
        stmt_existing = select(Reservation).where(Reservation.order_id == order_id)
        res_existing = await db.execute(stmt_existing)
        existing_res = res_existing.scalar_one_or_none()

        if existing_res:
            if existing_res.sector_id == sector_id and existing_res.quantity == quantity and existing_res.status == "RESERVED":
                # Idempotent response
                stmt_sec = select(Sector).where(Sector.id == sector_id)
                sec_res = await db.execute(stmt_sec)
                sec = sec_res.scalar_one()
                total = Decimal(str(sec.price)) * quantity
                return ReservationResponse(
                    status="RESERVED",
                    order_id=existing_res.order_id,
                    event_id=event_id,
                    sector_id=existing_res.sector_id,
                    quantity=existing_res.quantity,
                    unit_price=sec.price,
                    total_amount=total,
                    expires_at=existing_res.expires_at,
                )
            else:
                raise ReservationConflictException(
                    code="ORDER_ALREADY_RESERVED",
                    message="Ya existe una reserva previa para esta orden con parámetros distintos",
                )

        # Atomic query with SELECT ... FOR UPDATE
        stmt_sector = (
            select(Sector)
            .where(Sector.id == sector_id, Sector.event_id == event_id)
            .with_for_update()
        )
        result_sector = await db.execute(stmt_sector)
        sector = result_sector.scalar_one_or_none()

        if not sector:
            raise EventsNotFoundException("El evento o sector especificado no existe")

        if sector.available_spots < quantity:
            raise OutOfStockException(
                message="Cupos insuficientes en el sector seleccionado",
                available_spots=sector.available_spots,
            )

        # Deduct available spots atomically
        sector.available_spots -= quantity

        # Create reservation record valid for 10 minutes
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        reservation = Reservation(
            order_id=order_id,
            sector_id=sector_id,
            quantity=quantity,
            status="RESERVED",
            expires_at=expires_at,
        )
        db.add(reservation)

        await db.commit()

        total_amount = Decimal(str(sector.price)) * quantity
        return ReservationResponse(
            status="RESERVED",
            order_id=order_id,
            event_id=event_id,
            sector_id=sector_id,
            quantity=quantity,
            unit_price=sector.price,
            total_amount=total_amount,
            expires_at=expires_at,
        )

    @staticmethod
    async def release_spots(
        db: AsyncSession,
        event_id: uuid.UUID,
        order_id: uuid.UUID,
    ) -> ReleaseResponse:
        # Lock reservation record
        stmt_res = (
            select(Reservation)
            .where(Reservation.order_id == order_id)
            .with_for_update()
        )
        result_res = await db.execute(stmt_res)
        reservation = result_res.scalar_one_or_none()

        if not reservation:
            # Idempotent response if reservation doesn't exist
            return ReleaseResponse(
                status="RELEASED",
                order_id=order_id,
                message="No se encontró reserva o ya fue procesada",
            )

        if reservation.status == "RELEASED":
            return ReleaseResponse(
                status="RELEASED",
                order_id=order_id,
                message="Cupos liberados previamente",
            )

        if reservation.status == "CONFIRMED":
            raise ReservationConflictException(
                code="RESERVATION_CONFIRMED",
                message="No se pueden liberar cupos de una reserva confirmada",
            )

        # Lock sector and restore spots
        stmt_sector = (
            select(Sector)
            .where(Sector.id == reservation.sector_id)
            .with_for_update()
        )
        res_sector = await db.execute(stmt_sector)
        sector = res_sector.scalar_one_or_none()

        if sector:
            sector.available_spots = min(
                sector.capacity, sector.available_spots + reservation.quantity
            )

        reservation.status = "RELEASED"
        await db.commit()

        return ReleaseResponse(
            status="RELEASED",
            order_id=order_id,
            message="Cupos liberados exitosamente",
        )

    @staticmethod
    async def confirm_reservation(
        db: AsyncSession,
        event_id: uuid.UUID,
        order_id: uuid.UUID,
    ) -> ConfirmReservationResponse:
        stmt_res = (
            select(Reservation)
            .where(Reservation.order_id == order_id)
            .with_for_update()
        )
        result_res = await db.execute(stmt_res)
        reservation = result_res.scalar_one_or_none()

        if not reservation:
            raise EventsNotFoundException("Reserva no encontrada")

        if reservation.status == "RELEASED":
            raise ReservationConflictException(
                code="RESERVATION_ALREADY_RELEASED",
                message="La reserva ya fue liberada y no puede ser confirmada",
            )

        if reservation.status == "CONFIRMED":
            return ConfirmReservationResponse(
                status="CONFIRMED",
                order_id=order_id,
                message="Reserva ya confirmada previamente",
            )

        reservation.status = "CONFIRMED"
        await db.commit()

        return ConfirmReservationResponse(
            status="CONFIRMED",
            order_id=order_id,
            message="Reserva confirmada exitosamente",
        )
