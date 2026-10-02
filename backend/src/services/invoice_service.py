from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.models.booking import Booking
from src.models.invoice import Invoice


class InvoiceService:
    @staticmethod
    async def ensure_for_booking(
        db: AsyncSession,
        booking: Booking,
    ) -> Invoice:
        existing = await db.scalar(
            select(Invoice).where(Invoice.booking_id == booking.id)
        )
        if existing:
            return existing

        taxable = Decimal(booking.subtotal) + Decimal(booking.service_fee)
        rate = Decimal(str(settings.gst_rate_percent))
        gst = (taxable * rate / Decimal("100")).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
        invoice = Invoice(
            booking_id=booking.id,
            invoice_number=f"NEST-{booking.created_at:%Y%m%d}-{booking.id:06d}",
            taxable_amount=taxable,
            gst_rate=rate,
            gst_amount=gst,
            total_amount=(taxable + gst).quantize(Decimal("0.01")),
        )
        db.add(invoice)
        await db.commit()
        await db.refresh(invoice)
        return invoice
