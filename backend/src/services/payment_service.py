from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.models.booking import Booking, BookingStatus
from src.models.payment import Payment, PaymentStatus
from src.services.razorpay_service import RazorpayService


class PaymentService:
    @staticmethod
    async def create_for_booking(
        db: AsyncSession,
        booking: Booking,
        transfer_fee: Decimal = Decimal("0"),
    ) -> Payment:
        amount = booking.total_amount + transfer_fee
        provider = "razorpay" if settings.payment_provider == "razorpay" else "manual_demo"

        payment = Payment(
            booking_id=booking.id,
            provider=provider,
            amount=amount,
            currency="INR",
            status=PaymentStatus.PENDING,
        )

        if provider == "razorpay":
            order = await RazorpayService.create_order(
                amount,
                receipt=f"booking_{booking.id}",
            )
            payment.provider_order_id = order["id"]

        db.add(payment)
        await db.commit()
        await db.refresh(payment)
        return payment

    @staticmethod
    async def mark_paid(
        db: AsyncSession,
        payment: Payment,
        booking: Booking,
        provider_payment_id: str | None = None,
    ) -> Payment:
        if booking.status == BookingStatus.CANCELLED:
            if payment.provider == "razorpay" and provider_payment_id:
                await RazorpayService.refund_payment(
                    provider_payment_id,
                    payment.amount,
                )
                payment.provider_payment_id = provider_payment_id
                payment.status = PaymentStatus.REFUNDED
                payment.refund_amount = payment.amount
                payment.refunded_at = datetime.now(timezone.utc)
                await db.commit()
                await db.refresh(payment)
                return payment

            raise ValueError("Booking hold has expired and cannot be confirmed")

        payment.status = PaymentStatus.PAID
        payment.paid_at = datetime.now(timezone.utc)
        if provider_payment_id:
            payment.provider_payment_id = provider_payment_id

        booking.status = BookingStatus.CONFIRMED
        booking.expires_at = None

        await db.commit()
        await db.refresh(payment)
        return payment
