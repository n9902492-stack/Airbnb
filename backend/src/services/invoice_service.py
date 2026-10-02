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
        paid_total: Decimal,
    ) -> Invoice:
        existing = await db.scalar(
            select(Invoice).where(Invoice.booking_id == booking.id)
        )
        if existing:
            return existing

        rate = Decimal(str(settings.gst_rate_percent)) if settings.gst_enabled else Decimal("0")
        if rate > 0:
            divisor = Decimal("1") + rate / Decimal("100")
            taxable = (Decimal(paid_total) / divisor).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            )
            gst = (Decimal(paid_total) - taxable).quantize(Decimal("0.01"))
        else:
            taxable = Decimal(paid_total).quantize(Decimal("0.01"))
            gst = Decimal("0.00")

        invoice = Invoice(
            booking_id=booking.id,
            invoice_number=f"NEST-{booking.created_at:%Y%m%d}-{booking.id:06d}",
            taxable_amount=taxable,
            gst_rate=rate,
            gst_amount=gst,
            total_amount=Decimal(paid_total).quantize(Decimal("0.01")),
        )
        db.add(invoice)
        await db.commit()
        await db.refresh(invoice)
        return invoice
