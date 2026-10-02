from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReviewCreate(BaseModel):
    booking_id: int
    rating: int = Field(ge=1, le=5)
    comment: str = Field(min_length=10, max_length=1500)


class ReviewRead(BaseModel):
    id: int
    property_id: int
    booking_id: int
    guest_id: int
    rating: int
    comment: str
    created_at: datetime
    guest_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ReviewSummary(BaseModel):
    average_rating: float
    review_count: int
    reviews: list[ReviewRead]
