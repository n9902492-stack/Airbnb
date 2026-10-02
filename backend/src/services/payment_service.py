from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.models.booking import Booking, BookingStatus
from src.models.payment import Payment, PaymentStatus
from src.models.property import Property
from src.models.user import User
from src.services.email_service import EmailService
from src.services.invoice_service import InvoiceService
from src.services.notification_service import NotificationService
from src.services.payout_service import PayoutService
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

        await PayoutService.ensure_for_paid_booking(db, booking, payment.amount)
        await InvoiceService.ensure_for_booking(db, booking)

        property_obj = await db.get(Property, booking.property_id)
        guest = await db.get(User, booking.guest_id)

        if guest:
            await NotificationService.create(
                db,
                guest.id,
                "booking_confirmed",
                "Booking confirmed",
                f"Your booking #{booking.id} is confirmed.",
            )

        if property_obj:
            await NotificationService.create(
                db,
                property_obj.owner_id,
                "new_reservation",
                "New reservation",
                f"{property_obj.title} received booking #{booking.id}.",
            )

        if guest and property_obj:
            try:
                await EmailService.send_booking_confirmation(
                    guest.email,
                    property_obj.title,
                    str(booking.check_in),
                    str(booking.check_out),
                    f"{payment.amount:.2f}",
                )
            except Exception:
                pass

        return payment
