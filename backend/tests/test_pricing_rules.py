from datetime import date
from decimal import Decimal

import pytest

from src.models.property import Property
from src.services.pricing_service import PricingService


@pytest.mark.asyncio
async def test_stay_limits_are_enforced():
    property_obj = Property(
        owner_id=1,
        title="Test",
        description="Test property description",
        property_type="house",
        category="Mountain",
        address_line="Test",
        city="Test",
        state="Test",
        country="India",
        postal_code="000000",
        guests=2,
        bedrooms=1,
        beds=1,
        bathrooms=1,
        price_per_night=Decimal("1000"),
        cleaning_fee=Decimal("0"),
        minimum_stay_nights=2,
        maximum_stay_nights=5,
        amenities=[],
        house_rules=[],
        image_urls=[],
        check_in_time="14:00",
        check_out_time="11:00",
    )

    class EmptyResult:
        def scalars(self):
            return self
        def all(self):
            return []

    class FakeDb:
        async def execute(self, *_args, **_kwargs):
            return EmptyResult()

    with pytest.raises(ValueError):
        await PricingService.calculate_stay(
            FakeDb(),
            property_obj,
            date(2026, 10, 10),
            date(2026, 10, 11),
        )
