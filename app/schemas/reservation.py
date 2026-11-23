import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ReservationRequest(BaseModel):
    order_id: uuid.UUID = Field(..., description="UUID único de la orden generada en ms-orders")
    sector_id: uuid.UUID = Field(..., description="UUID del sector seleccionado")
    quantity: int = Field(..., ge=1, le=6, description="Cantidad de entradas a reservar (1 a 6)")


class ReservationResponse(BaseModel):
    status: str = Field(default="RESERVED")
    order_id: uuid.UUID
    event_id: uuid.UUID
    sector_id: uuid.UUID
    quantity: int
    unit_price: Decimal
    total_amount: Decimal
    expires_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReleaseRequest(BaseModel):
    order_id: uuid.UUID = Field(..., description="UUID de la orden cuyos cupos se liberarán")


class ReleaseResponse(BaseModel):
    status: str = Field(default="RELEASED")
    order_id: uuid.UUID
    message: str = Field(default="Cupos liberados exitosamente")


class ConfirmReservationRequest(BaseModel):
    order_id: uuid.UUID = Field(..., description="UUID de la orden pagada exitosamente")


class ConfirmReservationResponse(BaseModel):
    status: str = Field(default="CONFIRMED")
    order_id: uuid.UUID
    message: str = Field(default="Reserva confirmada exitosamente")


class OutOfStockResponse(BaseModel):
    code: str = "EVENTS_OUT_OF_STOCK"
    message: str = "Cupos insuficientes en el sector seleccionado"
    available_spots: int = 0


class NotFoundResponse(BaseModel):
    code: str = "EVENTS_NOT_FOUND"
    message: str = "El evento o sector especificado no existe"
