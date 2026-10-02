from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from src.models.property import PropertyStatus


class PropertyBase(BaseModel):
    title: str = Field(min_length=3, max_length=180)
    description: str = Field(min_length=20)
    property_type: str
    category: str

    address_line: str
    city: str
    state: str
    country: str = "India"
    postal_code: str
    latitude: float | None = None
    longitude: float | None = None

    guests: int = Field(ge=1)
    bedrooms: int = Field(ge=0)
    beds: int = Field(ge=1)
    bathrooms: int = Field(ge=1)

    price_per_night: Decimal = Field(gt=0)
    cleaning_fee: Decimal = Field(default=0, ge=0)
    weekend_price_per_night: Decimal | None = Field(default=None, gt=0)
    minimum_stay_nights: int = Field(default=1, ge=1, le=90)
    maximum_stay_nights: int | None = Field(default=None, ge=1, le=365)

    amenities: list[str] = []
    house_rules: list[str] = []
    image_urls: list[str] = []

    check_in_time: str = "14:00"
    check_out_time: str = "11:00"


class PropertyCreate(PropertyBase):
    pass


class PropertyUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    property_type: str | None = None
    category: str | None = None
    address_line: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    postal_code: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    guests: int | None = Field(default=None, ge=1)
    bedrooms: int | None = Field(default=None, ge=0)
    beds: int | None = Field(default=None, ge=1)
    bathrooms: int | None = Field(default=None, ge=1)
    price_per_night: Decimal | None = Field(default=None, gt=0)
    cleaning_fee: Decimal | None = Field(default=None, ge=0)
    weekend_price_per_night: Decimal | None = Field(default=None, gt=0)
    minimum_stay_nights: int | None = Field(default=None, ge=1, le=90)
    maximum_stay_nights: int | None = Field(default=None, ge=1, le=365)
    amenities: list[str] | None = None
    house_rules: list[str] | None = None
    image_urls: list[str] | None = None
    check_in_time: str | None = None
    check_out_time: str | None = None


class PropertyRead(PropertyBase):
    id: int
    owner_id: int
    status: PropertyStatus
    rejection_reason: str | None = None

    model_config = ConfigDict(from_attributes=True)
