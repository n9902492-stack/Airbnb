import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base


class TransferDirection(str, enum.Enum):
    PICKUP_TO_STAY = "pickup_to_stay"
    STAY_TO_DROPOFF = "stay_to_dropoff"


class TransferPlaceType(str, enum.Enum):
    AIRPORT = "airport"
    RAILWAY = "railway"
    BUS_STAND = "bus_stand"
    CUSTOM = "custom"


class TransferStatus(str, enum.Enum):
    REQUESTED = "requested"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class TransferRequest(Base):
    __tablename__ = "transfer_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int] = mapped_column(
        ForeignKey("bookings.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    guest_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    property_id: Mapped[int] = mapped_column(
        ForeignKey("properties.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    direction: Mapped[TransferDirection] = mapped_column(
        Enum(TransferDirection, name="transfer_direction"),
        nullable=False,
    )
    place_type: Mapped[TransferPlaceType] = mapped_column(
        Enum(TransferPlaceType, name="transfer_place_type"),
        nullable=False,
    )
    place_name: Mapped[str] = mapped_column(String(255), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    distance_km: Mapped[float] = mapped_column(Float, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(nullable=False)
    estimated_fare: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    status: Mapped[TransferStatus] = mapped_column(
        Enum(TransferStatus, name="transfer_status"),
        default=TransferStatus.REQUESTED,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    booking = relationship("Booking", back_populates="transfer")
    property = relationship("Property", back_populates="transfer_requests")
