from decimal import Decimal, ROUND_HALF_UP

from src.core.config import settings


class TaxService:
    @staticmethod
    def calculate(taxable_amount: Decimal) -> tuple[Decimal, Decimal]:
        if not settings.gst_enabled:
            return Decimal("0.00"), Decimal("0.00")

        rate = Decimal(str(settings.gst_rate_percent))
        gst = (
            taxable_amount
            * rate
            / Decimal("100")
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return rate, gst
