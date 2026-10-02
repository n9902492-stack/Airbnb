from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class OfferingCreate(BaseModel):
    kind: str = Field(pattern="^(service|experience)$")
    title: str = Field(min_length=3, max_length=180)
    description: str = Field(min_length=20)
    category: str = Field(min_length=2, max_length=80)
    city: str
    state: str
    country: str = "India"
    latitude: float | None = None
    longitude: float | None = None
    price: Decimal = Field(gt=0)
    pricing_unit: str = Field(default="per_guest", pattern="^(per_guest|per_group|per_session)$")
    duration_minutes: int = Field(default=60, ge=15, le=1440)
    capacity: int = Field(default=1, ge=1, le=100)
    image_urls: list[str] = []
    included_items: list[str] = []
    requirements: list[str] = []
    instant_book: bool = True


class OfferingBookingCreate(BaseModel):
    slot_id: int | None = None
    scheduled_at: datetime | None = None
    guest_count: int = Field(ge=1)
    private_group: bool = False
