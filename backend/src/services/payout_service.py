from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.models.booking import Booking
from src.models.payout import OwnerPayout, PayoutStatus
from src.models.property import Property


class PayoutService:
    @staticmethod
    async def ensure_for_paid_booking(
        db: AsyncSession,
        booking: Booking,
        paid_amount: Decimal,
    ) -> OwnerPayout:
        existing = await db.scalar(
            select(OwnerPayout).where(OwnerPayout.booking_id == booking.id)
        )
        if existing:
            return existing

        property_obj = await db.get(Property, booking.property_id)
        if not property_obj:
            raise ValueError("Property not found for payout")

        commission = (
            paid_amount
            * Decimal(str(settings.platform_commission_percent))
            / Decimal("100")
        ).quantize(Decimal("0.01"))

        payout = OwnerPayout(
            booking_id=booking.id,
            owner_id=property_obj.owner_id,
            gross_amount=paid_amount,
            platform_commission=commission,
            owner_amount=(paid_amount - commission).quantize(Decimal("0.01")),
            status=PayoutStatus.PENDING,
        )
        db.add(payout)
        await db.commit()
        await db.refresh(payout)
        return payout

    @staticmethod
    async def apply_refund(
        db: AsyncSession,
        booking_id: int,
        refund_amount: Decimal,
    ) -> None:
        payout = await db.scalar(
            select(OwnerPayout).where(OwnerPayout.booking_id == booking_id)
        )
        if not payout:
            return

        payout.refund_adjustment = refund_amount
        if payout.status in {PayoutStatus.PENDING, PayoutStatus.READY}:
            payout.owner_amount = max(
                Decimal("0"),
                payout.owner_amount - refund_amount,
            )
            if payout.owner_amount == 0:
                payout.status = PayoutStatus.CANCELLED

        await db.commit()


    @staticmethod
    async def mark_ready(db: AsyncSession, booking_id: int) -> None:
        payout = await db.scalar(
            select(OwnerPayout).where(OwnerPayout.booking_id == booking_id)
        )
        if payout and payout.status == PayoutStatus.PENDING:
            payout.status = PayoutStatus.READY
            await db.commit()

    @staticmethod
    async def mark_paid(
        db: AsyncSession,
        payout: OwnerPayout,
        provider_reference: str | None = None,
    ) -> OwnerPayout:
        from datetime import datetime, timezone

        payout.status = PayoutStatus.PAID
        payout.provider_reference = provider_reference
        payout.paid_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(payout)
        return payout
