from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


class BookingChangeRequest(Base):
    __tablename__ = "booking_change_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int] = mapped_column(
        ForeignKey("bookings.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    requested_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    new_check_in: Mapped[date] = mapped_column(Date, nullable=False)
    new_check_out: Mapped[date] = mapped_column(Date, nullable=False)
    new_guest_count: Mapped[int] = mapped_column(Integer, nullable=False)
    old_total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    new_total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    price_difference: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="requested", index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
