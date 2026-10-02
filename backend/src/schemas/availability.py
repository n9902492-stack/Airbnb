from datetime import date

from pydantic import BaseModel, Field, model_validator


class AvailabilityBlockCreate(BaseModel):
    start_date: date
    end_date: date
    reason: str = Field(default="Owner blocked", max_length=255)

    @model_validator(mode="after")
    def validate_range(self):
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self


class AvailabilityResponse(BaseModel):
    property_id: int
    blocked_dates: list[date]
