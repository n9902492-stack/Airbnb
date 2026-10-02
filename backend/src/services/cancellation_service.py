from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.models.booking import Booking, BookingStatus
from src.models.payment import Payment, PaymentStatus
from src.models.property import Property
from src.models.user import User
from src.services.email_service import EmailService
from src.services.notification_service import NotificationService
from src.services.payout_service import PayoutService
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
            if percent == 100:
                payment.status = PaymentStatus.REFUNDED

        booking.status = BookingStatus.CANCELLED
        booking.cancelled_at = datetime.now(timezone.utc)
        booking.cancellation_reason = reason

        await db.commit()

        if refund_amount > 0:
            await PayoutService.apply_refund(db, booking.id, percent)

        property_obj = await db.get(Property, booking.property_id)
        guest = await db.get(User, booking.guest_id)

        if guest:
            await NotificationService.create(
                db,
                guest.id,
                "booking_cancelled",
                "Booking cancelled",
                f"Booking #{booking.id} was cancelled. Refund: ₹{refund_amount:.2f}.",
            )

        if property_obj:
            await NotificationService.create(
                db,
                property_obj.owner_id,
                "reservation_cancelled",
                "Reservation cancelled",
                f"Booking #{booking.id} for {property_obj.title} was cancelled.",
            )

        if guest and property_obj:
            try:
                await EmailService.send_cancellation_receipt(
                    guest.email,
                    property_obj.title,
                    f"{refund_amount:.2f}",
                    percent,
                )
            except Exception:
                pass

        return percent, refund_amount
