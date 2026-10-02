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
from src.services.job_queue import JobQueue
from src.services.notification_service import NotificationService
from src.services.payout_service import PayoutService
from src.services.promotion_service import PromotionService
from src.services.razorpay_service import RazorpayService
from src.services.tax_service import TaxService


class PaymentService:
    @staticmethod
    async def create_for_booking(
        db: AsyncSession,
        booking: Booking,
        transfer_fee: Decimal = Decimal("0"),
        promo_code: str | None = None,
    ) -> Payment:
        pre_discount = Decimal(booking.total_amount) + transfer_fee
        promo, discount = await PromotionService.calculate_discount(
            db, promo_code, pre_discount
        )
        taxable_amount = max(Decimal("0"), pre_discount - discount)
        _, gst_amount = TaxService.calculate(taxable_amount)
        amount = taxable_amount + gst_amount

        booking.discount_amount = discount
        booking.promo_code = promo.code if promo else None
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
        await InvoiceService.ensure_for_booking(db, booking, payment.amount)
        await PromotionService.consume(db, booking)

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
            email_payload = {
                "email": guest.email,
                "property_title": property_obj.title,
                "check_in": str(booking.check_in),
                "check_out": str(booking.check_out),
                "amount": f"{payment.amount:.2f}",
            }
            queued = await JobQueue.enqueue(
                "booking_confirmation_email",
                email_payload,
            )
            if not queued:
                try:
                    await EmailService.send_booking_confirmation(**email_payload)
                except Exception:
                    pass

        return payment
