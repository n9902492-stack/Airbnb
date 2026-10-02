from decimal import Decimal

from src.core.config import settings
from src.services.tax_service import TaxService


def test_tax_disabled_by_default(monkeypatch):
    monkeypatch.setattr(settings, "gst_enabled", False)
    rate, amount = TaxService.calculate(Decimal("1000"))
    assert rate == Decimal("0.00")
    assert amount == Decimal("0.00")


def test_tax_calculation(monkeypatch):
    monkeypatch.setattr(settings, "gst_enabled", True)
    monkeypatch.setattr(settings, "gst_rate_percent", 18.0)
    rate, amount = TaxService.calculate(Decimal("1000"))
    assert rate == Decimal("18.0")
    assert amount == Decimal("180.00")
