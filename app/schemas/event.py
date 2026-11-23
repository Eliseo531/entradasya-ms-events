import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.sector import SectorCreate, SectorPublicResponse, SectorResponse


class EventBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=200, description="Título del evento")
    description: Optional[str] = Field(None, description="Descripción detallada del evento")
    venue: str = Field(..., min_length=2, max_length=200, description="Lugar o recinto del evento")
    event_date: datetime = Field(..., description="Fecha y hora de realización del evento")
    image_url: Optional[str] = Field(None, description="URL de la imagen o afiche promocional")


class EventCreate(EventBase):
    sectors: List[SectorCreate] = Field(..., min_length=1, description="Lista de sectores con capacidad y precio")


class EventUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    venue: Optional[str] = Field(None, min_length=2, max_length=200)
    event_date: Optional[datetime] = None
    image_url: Optional[str] = None


class EventStatusUpdate(BaseModel):
    status: Literal["PUBLISHED", "CANCELLED"]


class EventResponse(EventBase):
    id: uuid.UUID
    organizer_id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime
    sectors: List[SectorResponse] = []

    model_config = ConfigDict(from_attributes=True)


class EventPublicItem(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str] = None
    venue: str
    event_date: datetime
    image_url: Optional[str] = None
    status: str
    min_price: Optional[Decimal] = None
    sectors: List[SectorPublicResponse] = []

    model_config = ConfigDict(from_attributes=True)


class EventPublicListResponse(BaseModel):
    events: List[EventPublicItem]
    total: int
    page: int
    limit: int
    total_pages: int
