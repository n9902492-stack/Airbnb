from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.models.booking import BookingStatus


class BookingCreate(BaseModel):
    property_id: int
    check_in: date
    check_out: date
    guest_count: int = Field(ge=1)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.check_out <= self.check_in:
            raise ValueError("check_out must be after check_in")
        return self


class BookingRead(BaseModel):
    id: int
    property_id: int
    guest_id: int
    check_in: date
    check_out: date
    guest_count: int
    subtotal: Decimal
    service_fee: Decimal
    total_amount: Decimal
    status: BookingStatus

    model_config = ConfigDict(from_attributes=True)
