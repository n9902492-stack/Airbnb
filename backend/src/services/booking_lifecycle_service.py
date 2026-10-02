from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.booking import Booking, BookingStatus
from src.models.property import Property
from src.services.notification_service import NotificationService
from src.services.payout_service import PayoutService


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

    @staticmethod
    async def complete_finished_stays(db: AsyncSession) -> int:
        today = date.today()
        result = await db.execute(
            select(Booking).where(
                Booking.status == BookingStatus.CONFIRMED,
                Booking.check_out <= today,
            )
        )
        bookings = list(result.scalars().all())

        for booking in bookings:
            booking.status = BookingStatus.COMPLETED

        if not bookings:
            return 0

        await db.commit()

        for booking in bookings:
            await PayoutService.mark_ready(db, booking.id)

            property_obj = await db.get(Property, booking.property_id)
            await NotificationService.create(
                db,
                booking.guest_id,
                "review_available",
                "How was your stay?",
                f"Booking #{booking.id} is complete. You can now leave a verified review.",
            )

            if property_obj:
                await NotificationService.create(
                    db,
                    property_obj.owner_id,
                    "payout_ready",
                    "Payout ready",
                    f"Booking #{booking.id} is complete and its owner payout is ready.",
                )

        return len(bookings)
