from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import require_roles
from src.db.session import get_db
from src.models.booking import Booking
from src.models.property import Property
from src.models.user import User, UserRole
from src.schemas.property import PropertyCreate, PropertyRead, PropertyUpdate
from src.services.property_service import PropertyService


router = APIRouter()
owner_required = require_roles(UserRole.OWNER, UserRole.SUPER_ADMIN)


@router.get("/overview")
async def overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(owner_required),
):
    listing_count = await db.scalar(
        select(func.count(Property.id)).where(Property.owner_id == current_user.id)
    )
    booking_count = await db.scalar(
        select(func.count(Booking.id))
        .join(Property, Booking.property_id == Property.id)
        .where(Property.owner_id == current_user.id)
    )

    return {
        "active_listings": listing_count or 0,
        "total_bookings": booking_count or 0,
    }


@router.post("/properties", response_model=PropertyRead, status_code=status.HTTP_201_CREATED)
async def create_property(
    payload: PropertyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(owner_required),
):
    return await PropertyService.create_for_owner(db, current_user.id, payload)


@router.patch("/properties/{property_id}", response_model=PropertyRead)
async def update_property(
    property_id: int,
    payload: PropertyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(owner_required),
):
    property_obj = await PropertyService.get_by_id(db, property_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")

    if (
        current_user.role != UserRole.SUPER_ADMIN
        and property_obj.owner_id != current_user.id
    ):
        raise HTTPException(status_code=403, detail="Not your property")

    return await PropertyService.update(db, property_obj, payload)
