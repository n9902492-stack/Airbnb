from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user
from src.db.session import get_db
from src.models.booking import Booking, BookingStatus
from src.models.payment import Payment
from src.models.review import Review
from src.models.user import User
from src.models.property import PropertyStatus
from src.schemas.booking import BookingCreate, BookingRead
from src.services.booking_service import BookingService
from src.services.booking_lifecycle_service import BookingLifecycleService
from src.services.cancellation_service import CancellationService
from src.services.notification_service import NotificationService
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
        booking = await BookingService.create(db, current_user.id, property_obj, payload)
        if booking.status == BookingStatus.REQUESTED:
            await NotificationService.create(
                db,
                property_obj.owner_id,
                "booking_request",
                "New booking request",
                f"{current_user.full_name} requested {booking.check_in} to {booking.check_out} for {property_obj.title}.",
            )
        return booking
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.get("/my-trips")
async def my_trips(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await BookingLifecycleService.expire_unpaid(db)
    result = await db.execute(
        select(Booking)
        .where(Booking.guest_id == current_user.id)
        .order_by(Booking.created_at.desc())
    )
    bookings = list(result.scalars().all())

    items = []
    for booking in bookings:
        property_obj = await PropertyService.get_by_id(db, booking.property_id)
        payment = await db.scalar(
            select(Payment).where(Payment.booking_id == booking.id)
        )
        items.append({
            "id": booking.id,
            "property_id": booking.property_id,
            "property_title": property_obj.title if property_obj else "Property",
            "check_in": booking.check_in,
            "check_out": booking.check_out,
            "guest_count": booking.guest_count,
            "total_amount": float(booking.total_amount),
            "status": booking.status.value,
            "expires_at": booking.expires_at,
            "payment_status": payment.status.value if payment else None,
        })
    return items


@router.post("/{booking_id}/cancel")
async def cancel_booking(
    booking_id: int,
    reason: str = "Guest cancelled",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = await db.get(Booking, booking_id)
    if not booking or booking.guest_id != current_user.id:
        raise HTTPException(status_code=404, detail="Booking not found")

    payment = await db.scalar(
        select(Payment).where(Payment.booking_id == booking.id)
    )
    try:
        percent, refund = await CancellationService.cancel(
            db,
            booking,
            payment,
            reason,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    return {
        "booking_id": booking.id,
        "status": booking.status.value,
        "refund_amount": refund,
        "refund_percent": percent,
        "message": "Booking cancelled. Refund amount is based on the cancellation window.",
    }


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
