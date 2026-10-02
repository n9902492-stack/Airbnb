from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.booking import Booking
from src.models.promotion import PromotionCode
from src.models.promotion_redemption import PromotionRedemption


class PromotionService:
    @staticmethod
    async def calculate_discount(
        db: AsyncSession,
        code: str | None,
        amount: Decimal,
    ) -> tuple[PromotionCode | None, Decimal]:
        if not code:
            return None, Decimal("0")

        promo = await db.scalar(
            select(PromotionCode).where(
                PromotionCode.code == code.strip().upper(),
                PromotionCode.active.is_(True),
            )
        )
        if not promo:
            raise ValueError("Promotion code is invalid")

        now = datetime.now(timezone.utc)
        if promo.valid_from and promo.valid_from > now:
            raise ValueError("Promotion code is not active yet")
        if promo.valid_until and promo.valid_until < now:
            raise ValueError("Promotion code has expired")
        if promo.max_uses is not None and promo.used_count >= promo.max_uses:
            raise ValueError("Promotion code usage limit has been reached")
        if amount < promo.minimum_spend:
            raise ValueError(
                f"Minimum spend for this promotion is ₹{promo.minimum_spend}"
            )

        if promo.discount_type == "percent":
            discount = (
                amount * Decimal(promo.discount_value) / Decimal("100")
            ).quantize(Decimal("0.01"))
        else:
            discount = Decimal(promo.discount_value)

        discount = min(amount, max(Decimal("0"), discount))
        return promo, discount

    @staticmethod
    async def consume(
        db: AsyncSession,
        booking: Booking,
    ) -> None:
        if not booking.promo_code:
            return

        existing = await db.scalar(
            select(PromotionRedemption).where(
                PromotionRedemption.booking_id == booking.id
            )
        )
        if existing:
            return

        promo = await db.scalar(
            select(PromotionCode)
            .where(PromotionCode.code == booking.promo_code)
            .with_for_update()
        )
        if not promo:
            return

        db.add(
            PromotionRedemption(
                promotion_id=promo.id,
                booking_id=booking.id,
                user_id=booking.guest_id,
            )
        )
        promo.used_count += 1
        await db.commit()
