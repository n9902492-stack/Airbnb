from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user
from src.core.config import settings
from src.db.session import get_db
from src.models.booking import Booking, BookingStatus
from src.models.booking_change import BookingChangeRequest
from src.models.booking_change_payment import BookingChangePayment
from src.models.payment import Payment
from src.models.property import Property
from src.models.user import User
from src.services.availability_service import AvailabilityService
from src.services.cohost_service import CoHostService
from src.services.notification_service import NotificationService
from src.services.pricing_service import PricingService
from src.services.razorpay_service import RazorpayService


router = APIRouter()


class ChangeCreate(BaseModel):
    check_in: date
    check_out: date
    guest_count: int = Field(ge=1)


class VerifyAdjustment(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


async def _pricing(
    db: AsyncSession,
    property_obj: Property,
    check_in: date,
    check_out: date,
) -> Decimal:
    nightly, _ = await PricingService.calculate_stay(
        db, property_obj, check_in, check_out
    )
    subtotal = nightly + Decimal(property_obj.cleaning_fee)
    service_fee = (subtotal * Decimal("0.10")).quantize(Decimal("0.01"))
    return (subtotal + service_fee).quantize(Decimal("0.01"))


async def _apply_change(
    db: AsyncSession,
    change: BookingChangeRequest,
    booking: Booking,
) -> None:
    property_obj = await db.get(Property, booking.property_id)
    if not property_obj:
        raise ValueError("Property missing")

    nightly, _ = await PricingService.calculate_stay(
        db, property_obj, change.new_check_in, change.new_check_out
    )
    booking.check_in = change.new_check_in
    booking.check_out = change.new_check_out
    booking.guest_count = change.new_guest_count
    booking.subtotal = nightly + Decimal(property_obj.cleaning_fee)
    booking.service_fee = (booking.subtotal * Decimal("0.10")).quantize(Decimal("0.01"))
    booking.total_amount = change.new_total_amount
    change.status = "applied"
    change.decided_at = datetime.now(timezone.utc)
    await db.commit()


@router.post("/{booking_id}")
async def request_change(
    booking_id: int,
    payload: ChangeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = await db.get(Booking, booking_id)
    if not booking or booking.guest_id != current_user.id:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status != BookingStatus.CONFIRMED:
        raise HTTPException(status_code=409, detail="Only confirmed bookings can be changed")
    if payload.check_out <= payload.check_in:
        raise HTTPException(status_code=422, detail="Invalid dates")

    property_obj = await db.get(Property, booking.property_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    if payload.guest_count > property_obj.guests:
        raise HTTPException(status_code=422, detail="Guest count exceeds property capacity")

    available = await AvailabilityService.is_available(
        db,
        booking.property_id,
        payload.check_in,
        payload.check_out,
        exclude_booking_id=booking.id,
    )
    if not available:
        raise HTTPException(status_code=409, detail="Requested dates are not available")

    try:
        new_total = await _pricing(
            db, property_obj, payload.check_in, payload.check_out
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    change = BookingChangeRequest(
        booking_id=booking.id,
        requested_by_user_id=current_user.id,
        new_check_in=payload.check_in,
        new_check_out=payload.check_out,
        new_guest_count=payload.guest_count,
        old_total_amount=booking.total_amount,
        new_total_amount=new_total,
        price_difference=(new_total - Decimal(booking.total_amount)).quantize(Decimal("0.01")),
    )
    db.add(change)
    await db.commit()
    await db.refresh(change)

    await NotificationService.create(
        db,
        property_obj.owner_id,
        "booking_change_requested",
        "Reservation change requested",
        f"Booking #{booking.id} has a new date/guest request.",
    )
    return {
        "id": change.id,
        "status": change.status,
        "new_total_amount": float(change.new_total_amount),
        "price_difference": float(change.price_difference),
    }


@router.get("/mine/requests")
async def my_change_requests(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(BookingChangeRequest, Booking)
        .join(Booking, Booking.id == BookingChangeRequest.booking_id)
        .where(Booking.guest_id == current_user.id)
        .order_by(BookingChangeRequest.created_at.desc())
    )
    items = []
    for change, booking in result.all():
        adjustment = await db.scalar(
            select(BookingChangePayment).where(
                BookingChangePayment.change_request_id == change.id
            )
        )
        items.append({
            "id": change.id,
            "booking_id": booking.id,
            "new_check_in": change.new_check_in,
            "new_check_out": change.new_check_out,
            "new_guest_count": change.new_guest_count,
            "old_total_amount": float(change.old_total_amount),
            "new_total_amount": float(change.new_total_amount),
            "price_difference": float(change.price_difference),
            "status": change.status,
            "adjustment": (
                {
                    "id": adjustment.id,
                    "amount": float(adjustment.amount),
                    "provider": adjustment.provider,
                    "status": adjustment.status,
                    "provider_order_id": adjustment.provider_order_id,
                    "razorpay_key_id": settings.razorpay_key_id if adjustment.provider == "razorpay" else None,
                    "amount_paise": int(Decimal(adjustment.amount) * 100),
                }
                if adjustment
                else None
            ),
        })
    return items


@router.get("/host/requests")
async def host_change_requests(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(BookingChangeRequest, Booking, Property, User)
        .join(Booking, Booking.id == BookingChangeRequest.booking_id)
        .join(Property, Property.id == Booking.property_id)
        .join(User, User.id == Booking.guest_id)
        .where(BookingChangeRequest.status == "requested")
        .order_by(BookingChangeRequest.created_at.asc())
    )
    items = []
    for change, booking, property_obj, guest in result.all():
        permission = await CoHostService.permission_for(db, property_obj, current_user)
        if permission != "full":
            continue
        items.append({
            "id": change.id,
            "booking_id": booking.id,
            "property_title": property_obj.title,
            "guest_name": guest.full_name,
            "new_check_in": change.new_check_in,
            "new_check_out": change.new_check_out,
            "new_guest_count": change.new_guest_count,
            "price_difference": float(change.price_difference),
        })
    return items


@router.post("/{change_id}/accept")
async def accept_change(
    change_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    change = await db.get(BookingChangeRequest, change_id)
    if not change or change.status != "requested":
        raise HTTPException(status_code=404, detail="Change request not found")
    booking = await db.get(Booking, change.booking_id)
    property_obj = await db.get(Property, booking.property_id) if booking else None
    if not booking or not property_obj:
        raise HTTPException(status_code=404, detail="Booking not found")

    try:
        await CoHostService.require(db, property_obj, current_user, {"full"})
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))

    available = await AvailabilityService.is_available(
        db,
        booking.property_id,
        change.new_check_in,
        change.new_check_out,
        exclude_booking_id=booking.id,
    )
    if not available:
        change.status = "declined"
        await db.commit()
        raise HTTPException(status_code=409, detail="Requested dates are no longer available")

    difference = Decimal(change.price_difference)
    if difference > 0:
        provider = "razorpay" if settings.payment_provider == "razorpay" else "manual_demo"
        adjustment = BookingChangePayment(
            change_request_id=change.id,
            amount=difference,
            provider=provider,
        )
        if provider == "razorpay":
            order = await RazorpayService.create_order(
                difference,
                receipt=f"change_{change.id}",
            )
            adjustment.provider_order_id = order["id"]
        db.add(adjustment)
        change.status = "payment_required"
        await db.commit()
        await db.refresh(adjustment)
        await NotificationService.create(
            db,
            booking.guest_id,
            "booking_change_payment",
            "Reservation change approved",
            f"Pay the ₹{difference} difference to apply your booking change.",
        )
        return {
            "id": change.id,
            "status": change.status,
            "adjustment_payment_id": adjustment.id,
            "amount": float(difference),
            "provider": provider,
            "provider_order_id": adjustment.provider_order_id,
            "razorpay_key_id": settings.razorpay_key_id if provider == "razorpay" else None,
            "amount_paise": int(difference * 100),
        }

    if difference < 0:
        original_payment = await db.scalar(
            select(Payment).where(Payment.booking_id == booking.id)
        )
        refund = abs(difference)
        if (
            original_payment
            and original_payment.provider == "razorpay"
            and original_payment.provider_payment_id
        ):
            await RazorpayService.refund_payment(
                original_payment.provider_payment_id,
                refund,
            )
        if original_payment:
            original_payment.refund_amount = (
                Decimal(original_payment.refund_amount or 0) + refund
            )

    await _apply_change(db, change, booking)
    await NotificationService.create(
        db,
        booking.guest_id,
        "booking_change_accepted",
        "Reservation change accepted",
        f"Booking #{booking.id} was updated.",
    )
    return {"id": change.id, "status": change.status}


@router.post("/{change_id}/decline")
async def decline_change(
    change_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    change = await db.get(BookingChangeRequest, change_id)
    if not change or change.status != "requested":
        raise HTTPException(status_code=404, detail="Change request not found")
    booking = await db.get(Booking, change.booking_id)
    property_obj = await db.get(Property, booking.property_id) if booking else None
    if not booking or not property_obj:
        raise HTTPException(status_code=404, detail="Booking not found")
    try:
        await CoHostService.require(db, property_obj, current_user, {"full"})
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))

    change.status = "declined"
    change.decided_at = datetime.now(timezone.utc)
    await db.commit()
    await NotificationService.create(
        db,
        booking.guest_id,
        "booking_change_declined",
        "Reservation change declined",
        f"The change request for booking #{booking.id} was declined.",
    )
    return {"id": change.id, "status": change.status}


@router.post("/adjustments/{adjustment_id}/demo-confirm")
async def confirm_adjustment_demo(
    adjustment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    adjustment = await db.get(BookingChangePayment, adjustment_id)
    change = (
        await db.get(BookingChangeRequest, adjustment.change_request_id)
        if adjustment else None
    )
    booking = await db.get(Booking, change.booking_id) if change else None
    if not adjustment or not change or not booking or booking.guest_id != current_user.id:
        raise HTTPException(status_code=404, detail="Adjustment not found")
    if adjustment.provider != "manual_demo" or adjustment.status != "pending":
        raise HTTPException(status_code=409, detail="Adjustment cannot be confirmed")

    adjustment.status = "paid"
    adjustment.paid_at = datetime.now(timezone.utc)
    await _apply_change(db, change, booking)
    return {"id": change.id, "status": change.status}


@router.post("/adjustments/{adjustment_id}/verify-razorpay")
async def verify_adjustment(
    adjustment_id: int,
    payload: VerifyAdjustment,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    adjustment = await db.get(BookingChangePayment, adjustment_id)
    change = (
        await db.get(BookingChangeRequest, adjustment.change_request_id)
        if adjustment else None
    )
    booking = await db.get(Booking, change.booking_id) if change else None
    if not adjustment or not change or not booking or booking.guest_id != current_user.id:
        raise HTTPException(status_code=404, detail="Adjustment not found")
    if adjustment.provider_order_id != payload.razorpay_order_id:
        raise HTTPException(status_code=400, detail="Order mismatch")
    if not RazorpayService.verify_checkout_signature(
        payload.razorpay_order_id,
        payload.razorpay_payment_id,
        payload.razorpay_signature,
    ):
        raise HTTPException(status_code=400, detail="Invalid signature")

    adjustment.provider_payment_id = payload.razorpay_payment_id
    adjustment.status = "paid"
    adjustment.paid_at = datetime.now(timezone.utc)
    await _apply_change(db, change, booking)
    return {"id": change.id, "status": change.status}
