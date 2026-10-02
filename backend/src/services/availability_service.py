from datetime import date, timedelta

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.availability_block import AvailabilityBlock
from src.models.booking import Booking, BookingStatus


class AvailabilityService:
    BLOCKING_STATUSES = {BookingStatus.PENDING, BookingStatus.CONFIRMED}

    @classmethod
    async def is_available(
        cls,
        db: AsyncSession,
        property_id: int,
        check_in: date,
        check_out: date,
        exclude_booking_id: int | None = None,
    ) -> bool:
        booking_statement = select(Booking.id).where(
            Booking.property_id == property_id,
            Booking.status.in_(cls.BLOCKING_STATUSES),
            Booking.check_in < check_out,
            Booking.check_out > check_in,
        )
        if exclude_booking_id is not None:
            booking_statement = booking_statement.where(Booking.id != exclude_booking_id)

        booking_conflict = await db.scalar(booking_statement.limit(1))
        if booking_conflict:
            return False

        owner_block = await db.scalar(
            select(AvailabilityBlock.id)
            .where(
                AvailabilityBlock.property_id == property_id,
                AvailabilityBlock.start_date < check_out,
                AvailabilityBlock.end_date > check_in,
            )
            .limit(1)
        )
        return owner_block is None

    @classmethod
    async def blocked_dates(
        cls,
        db: AsyncSession,
        property_id: int,
        start: date,
        end: date,
    ) -> list[date]:
        result = await db.execute(
            select(Booking.check_in, Booking.check_out)
            .where(
                Booking.property_id == property_id,
                Booking.status.in_(cls.BLOCKING_STATUSES),
                Booking.check_in < end,
                Booking.check_out > start,
            )
        )
        ranges = list(result.all())

        block_result = await db.execute(
            select(AvailabilityBlock.start_date, AvailabilityBlock.end_date)
            .where(
                AvailabilityBlock.property_id == property_id,
                AvailabilityBlock.start_date < end,
                AvailabilityBlock.end_date > start,
            )
        )
        ranges.extend(block_result.all())

        dates: set[date] = set()
        for range_start, range_end in ranges:
            cursor = max(range_start, start)
            stop = min(range_end, end)
            while cursor < stop:
                dates.add(cursor)
                cursor += timedelta(days=1)
        return sorted(dates)
