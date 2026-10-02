from pydantic import BaseModel, Field

from src.models.transfer import TransferDirection, TransferPlaceType


class PlaceResult(BaseModel):
    name: str
    full_address: str
    latitude: float
    longitude: float
    stay_latitude: float | None = None
    stay_longitude: float | None = None


class TransferQuoteRequest(BaseModel):
    property_id: int
    direction: TransferDirection
    place_type: TransferPlaceType
    place_name: str
    latitude: float
    longitude: float


class TransferQuote(BaseModel):
    property_id: int
    direction: TransferDirection
    place_type: TransferPlaceType
    place_name: str
    latitude: float
    longitude: float
    distance_km: float
    duration_minutes: int
    estimated_fare: int
    currency: str = "INR"
    route_geometry: dict
    pricing_note: str


class TransferCreate(TransferQuoteRequest):
    booking_id: int


class TransferRead(BaseModel):
    id: int
    booking_id: int
    property_id: int
    direction: TransferDirection
    place_type: TransferPlaceType
    place_name: str
    distance_km: float
    duration_minutes: int
    estimated_fare: float
    status: str
