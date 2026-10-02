from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.booking import Booking
from src.models.property import Property
from src.schemas.booking import BookingCreate
from src.services.availability_service import AvailabilityService


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
        available = await AvailabilityService.is_available(
            db,
            property_obj.id,
            payload.check_in,
            payload.check_out,
        )
        if not available:
            raise ValueError("Selected dates are no longer available")

        nights = (payload.check_out - payload.check_in).days
        subtotal = property_obj.price_per_night * nights + property_obj.cleaning_fee
        service_fee = subtotal * cls.SERVICE_FEE_RATE
        total_amount = subtotal + service_fee

        booking = Booking(
            property_id=property_obj.id,
            guest_id=guest_id,
            check_in=payload.check_in,
            check_out=payload.check_out,
            guest_count=payload.guest_count,
            subtotal=subtotal,
            service_fee=service_fee,
            total_amount=total_amount,
        )
        db.add(booking)
        await db.commit()
        await db.refresh(booking)
        return booking
