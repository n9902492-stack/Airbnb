from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


class OfferingAvailabilitySlot(Base):
    __tablename__ = "offering_availability_slots"

    id: Mapped[int] = mapped_column(primary_key=True)
    offering_id: Mapped[int] = mapped_column(
        ForeignKey("marketplace_offerings.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    price_override: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    private_group_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    is_private_available: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
