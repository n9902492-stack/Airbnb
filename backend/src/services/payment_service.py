from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.booking import Booking, BookingStatus
from src.models.payment import Payment, PaymentStatus


class PaymentService:
    @staticmethod
    async def create_for_booking(
        db: AsyncSession,
        booking: Booking,
        transfer_fee: Decimal = Decimal("0"),
    ) -> Payment:
        amount = booking.total_amount + transfer_fee
        payment = Payment(
            booking_id=booking.id,
            amount=amount,
            currency="INR",
            status=PaymentStatus.PENDING,
        )
        db.add(payment)
        await db.commit()
        await db.refresh(payment)
        return payment

    @staticmethod
    async def mark_paid(db: AsyncSession, payment: Payment, booking: Booking) -> Payment:
        payment.status = PaymentStatus.PAID
        payment.paid_at = datetime.now(timezone.utc)
        booking.status = BookingStatus.CONFIRMED
        await db.commit()
        await db.refresh(payment)
        return payment
