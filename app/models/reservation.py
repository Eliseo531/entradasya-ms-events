import uuid
from datetime import datetime
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, nullable=False, unique=True, index=True
    )
    sector_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("sectors.id"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="RESERVED"
    )  # RESERVED, CONFIRMED, RELEASED
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    sector: Mapped["Sector"] = relationship("Sector", back_populates="reservations")

    __table_args__ = (
        CheckConstraint(
            "quantity > 0 AND quantity <= 6", name="chk_reservation_quantity"
        ),
        CheckConstraint(
            "status IN ('RESERVED', 'CONFIRMED', 'RELEASED')",
            name="chk_reservation_status",
        ),
    )
