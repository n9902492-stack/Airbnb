from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.models.booking import Booking, BookingStatus
from src.models.property import Property
from src.schemas.booking import BookingCreate
from src.services.availability_service import AvailabilityService
from src.services.pricing_service import PricingService


class BookingService:
    SERVICE_FEE_RATE = Decimal("0.10")

    @classmethod
    async def create(
        cls,
        db: AsyncSession,
        guest_id: int,
        property_obj: Property,
        payload: BookingCreate,
    ) -> Booking:
        await db.execute(
            select(Property)
            .where(Property.id == property_obj.id)
            .with_for_update()
        )

        available = await AvailabilityService.is_available(
            db,
            property_obj.id,
            payload.check_in,
            payload.check_out,
        )
        if not available:
            raise ValueError("Selected dates are no longer available")

        nightly_total, _ = await PricingService.calculate_stay(
            db,
            property_obj,
            payload.check_in,
            payload.check_out,
        )
        subtotal = nightly_total + property_obj.cleaning_fee
        service_fee = (subtotal * cls.SERVICE_FEE_RATE).quantize(Decimal("0.01"))
        total_amount = subtotal + service_fee

        request_mode = property_obj.booking_mode == "request"
        booking = Booking(
            property_id=property_obj.id,
            guest_id=guest_id,
            check_in=payload.check_in,
            check_out=payload.check_out,
            guest_count=payload.guest_count,
            subtotal=subtotal,
            service_fee=service_fee,
            total_amount=total_amount,
            status=BookingStatus.REQUESTED if request_mode else BookingStatus.PENDING,
            expires_at=None if request_mode else (
                datetime.now(timezone.utc)
                + timedelta(minutes=settings.booking_hold_minutes)
            ),
        )
        db.add(booking)
        await db.commit()
        await db.refresh(booking)
        return booking
