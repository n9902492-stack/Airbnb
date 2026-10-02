from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import require_roles
from src.db.session import get_db
from src.models.availability_block import AvailabilityBlock
from src.models.booking import Booking, BookingStatus
from src.models.payment import Payment, PaymentStatus
from src.models.payout import OwnerPayout
from src.models.payout_account import OwnerPayoutAccount
from src.models.pricing_rule import PricingRule
from src.models.property import Property
from src.models.user import User, UserRole
from src.models.cohost import PropertyCoHost
from src.schemas.availability import AvailabilityBlockCreate
from src.schemas.pricing import PricingRuleCreate
from src.schemas.property import PropertyCreate, PropertyRead, PropertyUpdate
from src.services.image_service import ImageService
from src.services.notification_service import NotificationService
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




@router.post("/booking-requests/{booking_id}/accept")
async def accept_booking_request(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(owner_required),
):
    booking = await db.get(Booking, booking_id)
    if not booking or booking.status != BookingStatus.REQUESTED:
        raise HTTPException(status_code=404, detail="Booking request not found")
    property_obj = await db.get(Property, booking.property_id)
    if not property_obj or (
        current_user.role != UserRole.SUPER_ADMIN
        and property_obj.owner_id != current_user.id
    ):
        raise HTTPException(status_code=403, detail="Not your booking request")

    from datetime import datetime, timedelta, timezone
    from src.core.config import settings
    from src.services.availability_service import AvailabilityService

    available = await AvailabilityService.is_available(
        db, booking.property_id, booking.check_in, booking.check_out
    )
    if not available:
        booking.status = BookingStatus.CANCELLED
        booking.cancellation_reason = "Dates became unavailable before host acceptance"
        await db.commit()
        raise HTTPException(status_code=409, detail="Dates are no longer available")

    booking.status = BookingStatus.PENDING
    booking.expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.booking_hold_minutes
    )
    await db.commit()
    await NotificationService.create(
        db,
        booking.guest_id,
        "booking_request_accepted",
        "Your booking request was accepted",
        f"Complete payment for booking #{booking.id} before the hold expires.",
    )
    return {"booking_id": booking.id, "status": booking.status.value, "expires_at": booking.expires_at}


@router.post("/booking-requests/{booking_id}/decline")
async def decline_booking_request(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(owner_required),
):
    booking = await db.get(Booking, booking_id)
    if not booking or booking.status != BookingStatus.REQUESTED:
        raise HTTPException(status_code=404, detail="Booking request not found")
    property_obj = await db.get(Property, booking.property_id)
    if not property_obj or (
        current_user.role != UserRole.SUPER_ADMIN
        and property_obj.owner_id != current_user.id
    ):
        raise HTTPException(status_code=403, detail="Not your booking request")

    booking.status = BookingStatus.CANCELLED
    booking.cancellation_reason = "Declined by host"
    await db.commit()
    await NotificationService.create(
        db,
        booking.guest_id,
        "booking_request_declined",
        "Booking request declined",
        f"The host declined booking request #{booking.id}.",
    )
    return {"booking_id": booking.id, "status": booking.status.value}

@router.get("/reservations")
async def owner_reservations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(owner_required),
):
    await BookingLifecycleService.expire_unpaid(db)
    cohost_property_ids = select(PropertyCoHost.property_id).where(
        PropertyCoHost.user_id == current_user.id,
        PropertyCoHost.permission.in_(["messages", "full"]),
    )
    result = await db.execute(
        select(Booking, Property, User)
        .join(Property, Booking.property_id == Property.id)
        .join(User, Booking.guest_id == User.id)
        .where(
            (Property.owner_id == current_user.id)
            | (Property.id.in_(cohost_property_ids))
        )
        .order_by(Booking.check_in.asc())
    )
    return [
        {
            "booking_id": booking.id,
            "property_id": property_obj.id,
            "property_title": property_obj.title,
            "guest_id": booking.guest_id,
            "guest_name": guest.full_name,
            "check_in": booking.check_in,
            "check_out": booking.check_out,
            "guest_count": booking.guest_count,
            "total_amount": float(booking.total_amount),
            "status": booking.status.value,
        }
        for booking, property_obj, guest in result.all()
    ]


@router.get("/properties/{property_id}/pricing-rules")
async def list_pricing_rules(
    property_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(owner_required),
):
    property_obj = await db.get(Property, property_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    if current_user.role != UserRole.SUPER_ADMIN and property_obj.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your property")

    result = await db.execute(
        select(PricingRule)
        .where(PricingRule.property_id == property_id)
        .order_by(PricingRule.start_date.asc())
    )
    return [
        {
            "id": rule.id,
            "name": rule.name,
            "start_date": rule.start_date,
            "end_date": rule.end_date,
            "nightly_rate": float(rule.nightly_rate),
            "minimum_stay_nights": rule.minimum_stay_nights,
        }
        for rule in result.scalars().all()
    ]


@router.post("/properties/{property_id}/pricing-rules")
async def create_pricing_rule(
    property_id: int,
    payload: PricingRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(owner_required),
):
    property_obj = await db.get(Property, property_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    if current_user.role != UserRole.SUPER_ADMIN and property_obj.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your property")

    rule = PricingRule(property_id=property_id, **payload.model_dump())
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return {
        "id": rule.id,
        "name": rule.name,
        "start_date": rule.start_date,
        "end_date": rule.end_date,
        "nightly_rate": float(rule.nightly_rate),
        "minimum_stay_nights": rule.minimum_stay_nights,
    }


@router.delete("/properties/{property_id}/pricing-rules/{rule_id}")
async def delete_pricing_rule(
    property_id: int,
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(owner_required),
):
    property_obj = await db.get(Property, property_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    if current_user.role != UserRole.SUPER_ADMIN and property_obj.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your property")

    rule = await db.get(PricingRule, rule_id)
    if rule and rule.property_id == property_id:
        await db.delete(rule)
        await db.commit()
    return {"ok": True}


@router.get("/payout-account")
async def get_payout_account(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(owner_required),
):
    account = await db.scalar(
        select(OwnerPayoutAccount).where(
            OwnerPayoutAccount.owner_id == current_user.id
        )
    )
    if not account:
        return {"configured": False, "provider": "razorpay_route"}

    return {
        "configured": True,
        "provider": account.provider,
        "linked_account_id": account.linked_account_id,
        "status": account.status,
    }


@router.get("/payouts")
async def owner_payouts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(owner_required),
):
    result = await db.execute(
        select(OwnerPayout)
        .where(OwnerPayout.owner_id == current_user.id)
        .order_by(OwnerPayout.created_at.desc())
    )
    items = list(result.scalars().all())
    return {
        "pending": sum(float(x.owner_amount) for x in items if x.status.value in {"pending", "ready", "processing"}),
        "paid": sum(float(x.owner_amount) for x in items if x.status.value == "paid"),
        "commission": sum(float(x.platform_commission) for x in items),
        "payouts": [
            {
                "id": x.id,
                "booking_id": x.booking_id,
                "gross_amount": float(x.gross_amount),
                "platform_commission": float(x.platform_commission),
                "owner_amount": float(x.owner_amount),
                "refund_adjustment": float(x.refund_adjustment),
                "status": x.status.value,
                "created_at": x.created_at,
                "paid_at": x.paid_at,
            }
            for x in items
        ],
    }


@router.get("/earnings")
async def owner_earnings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(owner_required),
):
    result = await db.execute(
        select(OwnerPayout)
        .where(OwnerPayout.owner_id == current_user.id)
        .order_by(OwnerPayout.created_at.desc())
    )
    payouts = list(result.scalars().all())

    return {
        "gross": sum(float(item.gross_amount) for item in payouts),
        "refunded": sum(float(item.refund_adjustment) for item in payouts),
        "net": sum(float(item.owner_amount) for item in payouts),
        "transactions": [
            {
                "booking_id": item.booking_id,
                "property_title": "",
                "amount": float(item.gross_amount),
                "refund_amount": float(item.refund_adjustment),
                "net_amount": float(item.owner_amount),
                "status": item.status.value,
                "created_at": item.created_at,
            }
            for item in payouts
        ],
    }


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
    cohost_ids = select(PropertyCoHost.property_id).where(
        PropertyCoHost.user_id == current_user.id
    )
    result = await db.execute(
        select(Property)
        .where(
            (Property.owner_id == current_user.id)
            | (Property.id.in_(cohost_ids))
        )
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
