from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import require_roles
from src.db.session import get_db
from src.models.availability_block import AvailabilityBlock
from src.models.booking import Booking
from src.models.property import Property
from src.models.user import User, UserRole
from src.schemas.availability import AvailabilityBlockCreate
from src.schemas.property import PropertyCreate, PropertyRead, PropertyUpdate
from src.services.image_service import ImageService
from src.services.property_service import PropertyService
from src.services.booking_lifecycle_service import BookingLifecycleService


router = APIRouter()
owner_required = require_roles(UserRole.OWNER, UserRole.SUPER_ADMIN)


@router.post("/uploads/images")
async def upload_property_image(
    file: UploadFile = File(...),
    _: User = Depends(owner_required),
):
    try:
        url = await ImageService.save_property_image(file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"url": url}


@router.post("/properties/{property_id}/availability-blocks")
async def create_availability_block(
    property_id: int,
    payload: AvailabilityBlockCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(owner_required),
):
    property_obj = await db.get(Property, property_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    if current_user.role != UserRole.SUPER_ADMIN and property_obj.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your property")

    block = AvailabilityBlock(
        property_id=property_id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        reason=payload.reason,
    )
    db.add(block)
    await db.commit()
    await db.refresh(block)
    return {
        "id": block.id,
        "property_id": block.property_id,
        "start_date": block.start_date,
        "end_date": block.end_date,
        "reason": block.reason,
    }


@router.get("/reservations")
async def owner_reservations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(owner_required),
):
    await BookingLifecycleService.expire_unpaid(db)
    result = await db.execute(
        select(Booking, Property)
        .join(Property, Booking.property_id == Property.id)
        .where(Property.owner_id == current_user.id)
        .order_by(Booking.check_in.asc())
    )
    return [
        {
            "booking_id": booking.id,
            "property_id": property_obj.id,
            "property_title": property_obj.title,
            "guest_id": booking.guest_id,
            "check_in": booking.check_in,
            "check_out": booking.check_out,
            "guest_count": booking.guest_count,
            "total_amount": float(booking.total_amount),
            "status": booking.status.value,
        }
        for booking, property_obj in result.all()
    ]


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


@router.get("/properties", response_model=list[PropertyRead])
async def list_owner_properties(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(owner_required),
):
    result = await db.execute(
        select(Property)
        .where(Property.owner_id == current_user.id)
        .order_by(Property.created_at.desc())
    )
    return list(result.scalars().all())


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
