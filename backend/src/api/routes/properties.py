from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.schemas.property import PropertyRead
from src.services.property_service import PropertyService


router = APIRouter()


@router.get("", response_model=list[PropertyRead])
async def list_properties(
    q: str | None = Query(default=None, max_length=120),
    city: str | None = Query(default=None, max_length=120),
    category: str | None = Query(default=None, max_length=80),
    guests: int | None = Query(default=None, ge=1),
    check_in: date | None = Query(default=None),
    check_out: date | None = Query(default=None),
    bedrooms: int | None = Query(default=None, ge=0),
    beds: int | None = Query(default=None, ge=1),
    bathrooms: int | None = Query(default=None, ge=1),
    property_type: str | None = Query(default=None, max_length=80),
    instant_book: bool | None = Query(default=None),
    guest_favorite: bool | None = Query(default=None),
    amenities: list[str] | None = Query(default=None),
    min_price: Decimal | None = Query(default=None, ge=0),
    max_price: Decimal | None = Query(default=None, ge=0),
    min_lat: float | None = Query(default=None, ge=-90, le=90),
    max_lat: float | None = Query(default=None, ge=-90, le=90),
    min_lng: float | None = Query(default=None, ge=-180, le=180),
    max_lng: float | None = Query(default=None, ge=-180, le=180),
    db: AsyncSession = Depends(get_db),
):
    return await PropertyService.list_live(
        db,
        q=q,
        city=city,
        category=category,
        guests=guests,
        check_in=check_in,
        check_out=check_out,
        bedrooms=bedrooms,
        beds=beds,
        bathrooms=bathrooms,
        property_type=property_type,
        instant_book=instant_book,
        guest_favorite=guest_favorite,
        amenities=amenities,
        min_price=min_price,
        max_price=max_price,
        min_lat=min_lat,
        max_lat=max_lat,
        min_lng=min_lng,
        max_lng=max_lng,
    )


@router.get("/{property_id}", response_model=PropertyRead)
async def get_property(
    property_id: int,
    db: AsyncSession = Depends(get_db),
):
    property_obj = await PropertyService.get_by_id(db, property_id)
    if not property_obj or property_obj.status.value != "live":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found",
        )
    return property_obj
