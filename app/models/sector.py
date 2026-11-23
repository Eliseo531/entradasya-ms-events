import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Sector(Base):
    __tablename__ = "sectors"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    event_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    available_spots: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    event: Mapped["Event"] = relationship("Event", back_populates="sectors")
    reservations: Mapped[List["Reservation"]] = relationship(
        "Reservation", back_populates="sector", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("capacity > 0", name="chk_capacity_positive"),
        CheckConstraint("available_spots >= 0", name="chk_available_spots_non_negative"),
        CheckConstraint("price >= 0", name="chk_price_non_negative"),
        CheckConstraint("available_spots <= capacity", name="chk_available_not_exceed_capacity"),
        Index("idx_sectors_event_id", "event_id"),
    )
