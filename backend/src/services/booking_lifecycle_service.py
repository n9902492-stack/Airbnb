from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.booking import Booking, BookingStatus


class BookingLifecycleService:
    @staticmethod
    async def expire_unpaid(db: AsyncSession) -> int:
        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(Booking).where(
                Booking.status == BookingStatus.PENDING,
                Booking.expires_at.is_not(None),
                Booking.expires_at <= now,
            )
        )
        bookings = list(result.scalars().all())
        for booking in bookings:
            booking.status = BookingStatus.CANCELLED
            booking.cancelled_at = now
            booking.cancellation_reason = "Payment hold expired"

        if bookings:
            await db.commit()
        return len(bookings)
