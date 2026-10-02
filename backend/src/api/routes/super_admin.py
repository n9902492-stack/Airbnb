from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import require_roles
from src.db.session import get_db
from src.models.booking import Booking, BookingStatus
from src.models.payment import Payment, PaymentStatus
from src.models.property import Property, PropertyStatus
from src.models.user import User, UserRole
from src.services.cancellation_service import CancellationService


router = APIRouter()
super_admin_required = require_roles(UserRole.SUPER_ADMIN)


@router.get("/overview")
async def overview(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(super_admin_required),
):
    users = await db.scalar(select(func.count(User.id)))
    owners = await db.scalar(
        select(func.count(User.id)).where(User.role == UserRole.OWNER)
    )
    listings = await db.scalar(select(func.count(Property.id)))
    bookings = await db.scalar(select(func.count(Booking.id)))

    return {
        "users": users or 0,
        "owners": owners or 0,
        "listings": listings or 0,
        "bookings": bookings or 0,
    }


@router.get("/bookings")
async def admin_bookings(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(super_admin_required),
):
    result = await db.execute(
        select(Booking, Property, User, Payment)
        .join(Property, Booking.property_id == Property.id)
        .join(User, Booking.guest_id == User.id)
        .outerjoin(Payment, Payment.booking_id == Booking.id)
        .order_by(Booking.created_at.desc())
        .limit(200)
    )
    return [
        {
            "booking_id": booking.id,
            "property_title": property_obj.title,
            "guest_name": guest.full_name,
            "check_in": booking.check_in,
            "check_out": booking.check_out,
            "status": booking.status.value,
            "total_amount": float(booking.total_amount),
            "payment_status": payment.status.value if payment else None,
            "refund_amount": float(payment.refund_amount or 0) if payment else 0,
        }
        for booking, property_obj, guest, payment in result.all()
    ]


@router.get("/properties/pending")
async def pending_properties(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(super_admin_required),
):
    result = await db.execute(
        select(Property)
        .where(Property.status == PropertyStatus.PENDING)
        .order_by(Property.created_at.asc())
    )
    return [
        {
            "id": item.id,
            "title": item.title,
            "owner_id": item.owner_id,
            "city": item.city,
            "state": item.state,
            "price_per_night": float(item.price_per_night),
            "image_urls": item.image_urls,
            "created_at": item.created_at,
        }
        for item in result.scalars().all()
    ]


@router.post("/bookings/{booking_id}/cancel")
async def admin_cancel_booking(
    booking_id: int,
    reason: str = "Cancelled by platform administrator",
    db: AsyncSession = Depends(get_db),
    _: User = Depends(super_admin_required),
):
    booking = await db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.status in {BookingStatus.CANCELLED, BookingStatus.COMPLETED}:
        raise HTTPException(status_code=409, detail="Booking cannot be cancelled")

    payment = await db.scalar(
        select(Payment).where(Payment.booking_id == booking.id)
    )
    try:
        refund_percent, refund_amount = await CancellationService.cancel(
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
        "refund_percent": refund_percent,
        "refund_amount": refund_amount,
    }


@router.post("/properties/{property_id}/approve")
async def approve_property(
    property_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(super_admin_required),
):
    property_obj = await db.get(Property, property_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")

    property_obj.status = PropertyStatus.LIVE
    property_obj.rejection_reason = None
    await db.commit()

    return {"id": property_obj.id, "status": property_obj.status}


@router.post("/properties/{property_id}/reject")
async def reject_property(
    property_id: int,
    reason: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(super_admin_required),
):
    property_obj = await db.get(Property, property_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")

    property_obj.status = PropertyStatus.REJECTED
    property_obj.rejection_reason = reason
    await db.commit()

    return {"id": property_obj.id, "status": property_obj.status}
