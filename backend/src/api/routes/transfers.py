from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user
from src.db.session import get_db
from src.models.booking import Booking
from src.models.property import Property
from src.models.transfer import TransferRequest
from src.models.user import User
from src.schemas.transfer import (
    PlaceResult,
    TransferCreate,
    TransferQuote,
    TransferQuoteRequest,
    TransferRead,
)
from src.services.map_service import MapService


router = APIRouter()


@router.get("/places", response_model=list[PlaceResult])
async def search_places(
    q: str = Query(min_length=2, max_length=120),
    property_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    proximity = None
    if property_id:
        property_obj = await db.get(Property, property_id)
        if property_obj and property_obj.latitude is not None and property_obj.longitude is not None:
            proximity = (property_obj.latitude, property_obj.longitude)

    try:
        return await MapService.geocode(q, proximity)
    except (ValueError, Exception) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/quote", response_model=TransferQuote)
async def quote_transfer(
    payload: TransferQuoteRequest,
    db: AsyncSession = Depends(get_db),
):
    property_obj = await db.get(Property, payload.property_id)
    if property_obj and property_obj.latitude is not None and property_obj.longitude is not None:
        stay = (property_obj.latitude, property_obj.longitude)
    elif payload.stay_latitude is not None and payload.stay_longitude is not None:
        stay = (payload.stay_latitude, payload.stay_longitude)
    else:
        raise HTTPException(status_code=400, detail="Property map location is not configured")
    selected = (payload.latitude, payload.longitude)

    origin, destination = (
        (selected, stay)
        if payload.direction.value == "pickup_to_stay"
        else (stay, selected)
    )

    try:
        route = await MapService.route(origin, destination)
    except (ValueError, Exception) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    fare = MapService.calculate_fare(route["distance_km"], payload.place_type)
    return {
        **payload.model_dump(),
        **route,
        "estimated_fare": fare,
        "currency": "INR",
        "pricing_note": "Estimated private-transfer fare. Final fare may change if route, waiting time, tolls, parking, or pickup details change.",
    }


@router.post("", response_model=TransferRead)
async def add_transfer_to_booking(
    payload: TransferCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = await db.get(Booking, payload.booking_id)
    if not booking or booking.guest_id != current_user.id:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.property_id != payload.property_id:
        raise HTTPException(status_code=400, detail="Property does not match booking")

    existing = await db.scalar(select(TransferRequest.id).where(TransferRequest.booking_id == payload.booking_id))
    if existing:
        raise HTTPException(status_code=409, detail="This booking already has a transfer request")

    quote = await quote_transfer(payload, db)
    transfer = TransferRequest(
        booking_id=booking.id,
        guest_id=current_user.id,
        property_id=payload.property_id,
        direction=payload.direction,
        place_type=payload.place_type,
        place_name=payload.place_name,
        latitude=payload.latitude,
        longitude=payload.longitude,
        distance_km=quote.distance_km,
        duration_minutes=quote.duration_minutes,
        estimated_fare=quote.estimated_fare,
    )
    db.add(transfer)
    await db.commit()
    await db.refresh(transfer)
    return {
        "id": transfer.id,
        "booking_id": transfer.booking_id,
        "property_id": transfer.property_id,
        "direction": transfer.direction,
        "place_type": transfer.place_type,
        "place_name": transfer.place_name,
        "distance_km": transfer.distance_km,
        "duration_minutes": transfer.duration_minutes,
        "estimated_fare": float(transfer.estimated_fare),
        "status": transfer.status.value,
    }
