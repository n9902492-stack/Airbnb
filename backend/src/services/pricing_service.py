from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.pricing_rule import PricingRule
from src.models.property import Property


class PricingService:
    @staticmethod
    async def calculate_stay(
        db: AsyncSession,
        property_obj: Property,
        check_in: date,
        check_out: date,
    ) -> tuple[Decimal, list[dict]]:
        nights = (check_out - check_in).days
        if nights < property_obj.minimum_stay_nights:
            raise ValueError(
                f"Minimum stay is {property_obj.minimum_stay_nights} night(s)"
            )
        if property_obj.maximum_stay_nights and nights > property_obj.maximum_stay_nights:
            raise ValueError(
                f"Maximum stay is {property_obj.maximum_stay_nights} night(s)"
            )

        result = await db.execute(
            select(PricingRule)
            .where(
                PricingRule.property_id == property_obj.id,
                PricingRule.start_date < check_out,
                PricingRule.end_date >= check_in,
            )
            .order_by(PricingRule.created_at.desc())
        )
        rules = list(result.scalars().all())

        total = Decimal("0")
        breakdown: list[dict] = []
        cursor = check_in

        while cursor < check_out:
            matching = next(
                (
                    rule
                    for rule in rules
                    if rule.start_date <= cursor <= rule.end_date
                ),
                None,
            )

            rate = matching.nightly_rate if matching else property_obj.price_per_night
            if cursor.weekday() in {4, 5} and not matching:
                rate = property_obj.weekend_price_per_night or rate

            if matching and matching.minimum_stay_nights:
                if nights < matching.minimum_stay_nights:
                    raise ValueError(
                        f"{matching.name} requires at least "
                        f"{matching.minimum_stay_nights} nights"
                    )

            total += rate
            breakdown.append(
                {
                    "date": cursor,
                    "rate": rate,
                    "rule": matching.name if matching else None,
                }
            )
            cursor += timedelta(days=1)

        return total, breakdown
