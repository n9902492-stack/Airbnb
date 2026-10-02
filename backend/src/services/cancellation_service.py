from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.models.booking import Booking, BookingStatus
from src.models.payment import Payment, PaymentStatus
from src.services.razorpay_service import RazorpayService


class CancellationService:
    @staticmethod
    def refund_percent(booking: Booking) -> int:
        check_in = datetime.combine(
            booking.check_in,
            datetime.min.time(),
            tzinfo=timezone.utc,
        )
        hours = (check_in - datetime.now(timezone.utc)).total_seconds() / 3600

        if hours >= settings.cancellation_full_refund_hours:
            return 100
        if hours >= settings.cancellation_partial_refund_hours:
            return settings.cancellation_partial_refund_percent
        return 0

    @classmethod
    async def cancel(
        cls,
        db: AsyncSession,
        booking: Booking,
        payment: Payment | None,
        reason: str,
    ) -> tuple[int, Decimal]:
        if booking.status in {BookingStatus.CANCELLED, BookingStatus.COMPLETED}:
            raise ValueError("This booking cannot be cancelled")

        percent = cls.refund_percent(booking)
        refund_amount = Decimal("0")

        if payment and payment.status == PaymentStatus.PAID and percent > 0:
            refund_amount = (payment.amount * Decimal(percent) / Decimal("100")).quantize(Decimal("0.01"))

            if payment.provider == "razorpay" and payment.provider_payment_id:
                await RazorpayService.refund_payment(
                    payment.provider_payment_id,
                    refund_amount,
                )

            payment.refund_amount = refund_amount
            payment.refunded_at = datetime.now(timezone.utc)
            payment.status = PaymentStatus.REFUNDED

        booking.status = BookingStatus.CANCELLED
        booking.cancelled_at = datetime.now(timezone.utc)
        booking.cancellation_reason = reason

        await db.commit()
        return percent, refund_amount
