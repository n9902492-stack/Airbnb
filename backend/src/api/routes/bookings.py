from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user
from src.db.session import get_db
from src.models.booking import Booking, BookingStatus
from src.models.review import Review
from src.models.user import User
from src.models.property import PropertyStatus
from src.schemas.booking import BookingCreate, BookingRead
from src.services.booking_service import BookingService
from src.services.property_service import PropertyService


router = APIRouter()


@router.post("", response_model=BookingRead, status_code=status.HTTP_201_CREATED)
async def create_booking(
    payload: BookingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    property_obj = await PropertyService.get_by_id(db, payload.property_id)
    if not property_obj or property_obj.status != PropertyStatus.LIVE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property is not available",
        )

    if payload.guest_count > property_obj.guests:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Guest count exceeds this property's capacity",
        )

    try:
        return await BookingService.create(db, current_user.id, property_obj, payload)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.get("/reviewable")
async def reviewable_bookings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reviewed_booking_ids = select(Review.booking_id)

    result = await db.execute(
        select(Booking)
        .where(
            Booking.guest_id == current_user.id,
            Booking.status == BookingStatus.COMPLETED,
            Booking.id.not_in(reviewed_booking_ids),
        )
        .order_by(Booking.check_out.desc())
    )

    return [
        {
            "id": booking.id,
            "property_id": booking.property_id,
            "check_in": booking.check_in,
            "check_out": booking.check_out,
        }
        for booking in result.scalars().all()
    ]
