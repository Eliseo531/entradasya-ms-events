import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class SectorBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Nombre del sector (VIP, General, etc.)")
    capacity: int = Field(..., gt=0, description="Aforo total del sector")
    price: Decimal = Field(..., ge=0, description="Precio unitario de la entrada")


class SectorCreate(SectorBase):
    pass


class SectorResponse(SectorBase):
    id: uuid.UUID
    event_id: uuid.UUID
    available_spots: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SectorPublicResponse(BaseModel):
    id: uuid.UUID
    name: str
    capacity: int
    available_spots: int
    price: Decimal

    model_config = ConfigDict(from_attributes=True)
