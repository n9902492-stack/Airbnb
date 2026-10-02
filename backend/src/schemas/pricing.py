from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator


class PricingRuleCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    start_date: date
    end_date: date
    nightly_rate: Decimal = Field(gt=0)
    minimum_stay_nights: int | None = Field(default=None, ge=1, le=90)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self
