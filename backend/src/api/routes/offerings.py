from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user, require_roles
from src.core.config import settings
from src.db.session import get_db
from src.models.offering import MarketplaceOffering
from src.models.offering_booking import OfferingBooking
from src.models.user import User, UserRole
from src.schemas.offering import OfferingBookingCreate, OfferingCreate
from src.services.razorpay_service import RazorpayService


router = APIRouter()
host_required = require_roles(UserRole.OWNER, UserRole.SUPER_ADMIN)


def serialize(item: MarketplaceOffering) -> dict:
    return {
        "id": item.id,
        "host_id": item.host_id,
        "kind": item.kind,
        "title": item.title,
        "description": item.description,
        "category": item.category,
        "city": item.city,
        "state": item.state,
        "country": item.country,
        "latitude": item.latitude,
        "longitude": item.longitude,
        "price": float(item.price),
        "pricing_unit": item.pricing_unit,
        "duration_minutes": item.duration_minutes,
        "capacity": item.capacity,
        "image_urls": item.image_urls,
        "included_items": item.included_items,
        "requirements": item.requirements,
        "instant_book": item.instant_book,
        "status": item.status,
    }


@router.get("")
async def list_offerings(
    kind: str | None = Query(default=None, pattern="^(service|experience)$"),
    q: str | None = Query(default=None, max_length=120),
    city: str | None = Query(default=None, max_length=120),
    category: str | None = Query(default=None, max_length=80),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(MarketplaceOffering).where(MarketplaceOffering.status == "live")
    if kind:
        stmt = stmt.where(MarketplaceOffering.kind == kind)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(
            MarketplaceOffering.title.ilike(like),
            MarketplaceOffering.description.ilike(like),
            MarketplaceOffering.city.ilike(like),
        ))
    if city:
        stmt = stmt.where(MarketplaceOffering.city.ilike(f"%{city.strip()}%"))
    if category:
        stmt = stmt.where(MarketplaceOffering.category.ilike(category.strip()))

    result = await db.execute(stmt.order_by(MarketplaceOffering.created_at.desc()))
    return [serialize(x) for x in result.scalars().all()]


@router.get("/{offering_id}")
async def get_offering(offering_id: int, db: AsyncSession = Depends(get_db)):
    item = await db.get(MarketplaceOffering, offering_id)
    if not item or item.status != "live":
        raise HTTPException(status_code=404, detail="Offering not found")
    return serialize(item)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_offering(
    payload: OfferingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(host_required),
):
    item = MarketplaceOffering(
        host_id=current_user.id,
        status="pending",
        **payload.model_dump(),
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return serialize(item)


@router.get("/host/mine")
async def host_offerings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(host_required),
):
    result = await db.execute(
        select(MarketplaceOffering)
        .where(MarketplaceOffering.host_id == current_user.id)
        .order_by(MarketplaceOffering.created_at.desc())
    )
    return [serialize(x) for x in result.scalars().all()]


@router.post("/{offering_id}/book")
async def book_offering(
    offering_id: int,
    payload: OfferingBookingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = await db.get(MarketplaceOffering, offering_id)
    if not item or item.status != "live":
        raise HTTPException(status_code=404, detail="Offering not found")
    if payload.guest_count > item.capacity:
        raise HTTPException(status_code=422, detail="Guest count exceeds capacity")
    if payload.scheduled_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=422, detail="Choose a future time")

    units = payload.guest_count if item.pricing_unit == "per_guest" else 1
    subtotal = Decimal(item.price) * units
    service_fee = (subtotal * Decimal("0.10")).quantize(Decimal("0.01"))
    total = subtotal + service_fee

    booking = OfferingBooking(
        offering_id=item.id,
        guest_id=current_user.id,
        scheduled_at=payload.scheduled_at,
        guest_count=payload.guest_count,
        subtotal=subtotal,
        service_fee=service_fee,
        total_amount=total,
        status="confirmed" if item.instant_book else "requested",
        payment_status="unpaid",
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)

    if not item.instant_book:
        return {
            "id": booking.id,
            "status": booking.status,
            "payment_status": booking.payment_status,
            "message": "Request sent to host. Payment opens after acceptance.",
        }

    provider = "razorpay" if settings.payment_provider == "razorpay" else "manual_demo"
    booking.provider = provider
    if provider == "razorpay":
        order = await RazorpayService.create_order(total, receipt=f"offering_{booking.id}")
        booking.provider_order_id = order["id"]
        await db.commit()

    return {
        "id": booking.id,
        "status": booking.status,
        "payment_status": booking.payment_status,
        "amount": float(total),
        "currency": "INR",
        "provider": provider,
        "provider_order_id": booking.provider_order_id,
        "razorpay_key_id": settings.razorpay_key_id if provider == "razorpay" else None,
        "amount_paise": int(total * 100),
    }


@router.post("/bookings/{booking_id}/demo-confirm")
async def confirm_offering_demo(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = await db.get(OfferingBooking, booking_id)
    if not booking or booking.guest_id != current_user.id:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.provider != "manual_demo" or booking.status != "confirmed":
        raise HTTPException(status_code=409, detail="Booking is not ready for demo payment")
    booking.payment_status = "paid"
    await db.commit()
    return {"id": booking.id, "payment_status": booking.payment_status}


@router.post("/bookings/{booking_id}/verify-razorpay")
async def verify_offering_payment(
    booking_id: int,
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = await db.get(OfferingBooking, booking_id)
    if not booking or booking.guest_id != current_user.id:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.provider_order_id != razorpay_order_id:
        raise HTTPException(status_code=400, detail="Order mismatch")
    if not RazorpayService.verify_checkout_signature(
        razorpay_order_id, razorpay_payment_id, razorpay_signature
    ):
        raise HTTPException(status_code=400, detail="Invalid payment signature")
    booking.provider_payment_id = razorpay_payment_id
    booking.payment_status = "paid"
    await db.commit()
    return {"id": booking.id, "payment_status": "paid"}


@router.get("/bookings/mine")
async def my_offering_bookings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(OfferingBooking, MarketplaceOffering)
        .join(MarketplaceOffering, OfferingBooking.offering_id == MarketplaceOffering.id)
        .where(OfferingBooking.guest_id == current_user.id)
        .order_by(OfferingBooking.scheduled_at.asc())
    )
    return [
        {
            "id": b.id,
            "offering_id": o.id,
            "title": o.title,
            "kind": o.kind,
            "scheduled_at": b.scheduled_at,
            "guest_count": b.guest_count,
            "total_amount": float(b.total_amount),
            "status": b.status,
            "payment_status": b.payment_status,
        }
        for b, o in result.all()
    ]
