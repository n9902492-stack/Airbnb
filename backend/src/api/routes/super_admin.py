from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import require_roles
from src.db.session import get_db
from src.models.audit_log import AuditLog
from src.models.booking import Booking, BookingStatus
from src.models.payment import Payment, PaymentStatus
from src.models.payout import OwnerPayout, PayoutStatus
from src.models.payout_account import OwnerPayoutAccount
from src.models.property import Property, PropertyStatus
from src.models.user import User, UserRole
from src.schemas.payout import PayoutAccountUpdate
from src.services.audit_service import AuditService
from src.services.cancellation_service import CancellationService
from src.services.payout_service import PayoutService


router = APIRouter()
super_admin_required = require_roles(UserRole.SUPER_ADMIN)


@router.get("/audit-logs")
async def audit_logs(
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(super_admin_required),
):
    limit = min(max(limit, 1), 500)
    result = await db.execute(
        select(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    return [
        {
            "id": item.id,
            "actor_user_id": item.actor_user_id,
            "action": item.action,
            "entity_type": item.entity_type,
            "entity_id": item.entity_id,
            "request_id": item.request_id,
            "ip_address": item.ip_address,
            "metadata": item.metadata_json,
            "created_at": item.created_at,
        }
        for item in result.scalars().all()
    ]


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


@router.put("/owners/{owner_id}/payout-account")
async def set_owner_payout_account(
    owner_id: int,
    payload: PayoutAccountUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(super_admin_required),
):
    owner = await db.get(User, owner_id)
    if not owner or owner.role != UserRole.OWNER:
        raise HTTPException(status_code=404, detail="Owner not found")

    account = await db.scalar(
        select(OwnerPayoutAccount).where(
            OwnerPayoutAccount.owner_id == owner_id
        )
    )
    if account:
        account.linked_account_id = payload.linked_account_id
        account.status = "active"
    else:
        account = OwnerPayoutAccount(
            owner_id=owner_id,
            linked_account_id=payload.linked_account_id,
            status="active",
        )
        db.add(account)

    await db.commit()
    await db.refresh(account)
    await AuditService.record(
        db,
        "owner_payout_account.updated",
        actor_user_id=current_admin.id,
        entity_type="owner",
        entity_id=owner_id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        metadata={"provider": account.provider},
    )
    return {
        "owner_id": owner_id,
        "provider": account.provider,
        "linked_account_id": account.linked_account_id,
        "status": account.status,
    }


@router.get("/finance")
async def finance_overview(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(super_admin_required),
):
    payments = list((await db.execute(select(Payment))).scalars().all())
    payouts = list((await db.execute(select(OwnerPayout))).scalars().all())

    collected = sum(float(p.amount) for p in payments if p.status in {PaymentStatus.PAID, PaymentStatus.REFUNDED})
    refunds = sum(float(p.refund_amount or 0) for p in payments)
    commission = sum(float(p.platform_commission) for p in payouts)
    owner_payable = sum(float(p.owner_amount) for p in payouts if p.status in {PayoutStatus.PENDING, PayoutStatus.READY, PayoutStatus.PROCESSING})
    owner_paid = sum(float(p.owner_amount) for p in payouts if p.status == PayoutStatus.PAID)

    return {
        "collected": collected,
        "refunds": refunds,
        "platform_commission": commission,
        "owner_payable": owner_payable,
        "owner_paid": owner_paid,
        "payouts": [
            {
                "id": p.id,
                "booking_id": p.booking_id,
                "owner_id": p.owner_id,
                "owner_amount": float(p.owner_amount),
                "platform_commission": float(p.platform_commission),
                "status": p.status.value,
            }
            for p in payouts
        ],
    }


@router.post("/payouts/{payout_id}/mark-paid")
async def mark_payout_paid(
    payout_id: int,
    request: Request,
    provider_reference: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(super_admin_required),
):
    payout = await db.get(OwnerPayout, payout_id)
    if not payout:
        raise HTTPException(status_code=404, detail="Payout not found")
    if payout.status not in {PayoutStatus.READY, PayoutStatus.PROCESSING}:
        raise HTTPException(status_code=409, detail="Payout is not ready")

    payout = await PayoutService.mark_paid(db, payout, provider_reference)
    await AuditService.record(
        db,
        "payout.marked_paid",
        actor_user_id=current_admin.id,
        entity_type="owner_payout",
        entity_id=payout.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        metadata={"provider_reference": provider_reference},
    )
    return {"id": payout.id, "status": payout.status.value}


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
    request: Request,
    reason: str = "Cancelled by platform administrator",
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(super_admin_required),
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

    await AuditService.record(
        db,
        "booking.admin_cancelled",
        actor_user_id=current_admin.id,
        entity_type="booking",
        entity_id=booking.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        metadata={"reason": reason, "refund_amount": str(refund_amount)},
    )

    return {
        "booking_id": booking.id,
        "status": booking.status.value,
        "refund_percent": refund_percent,
        "refund_amount": refund_amount,
    }


@router.post("/properties/{property_id}/approve")
async def approve_property(
    property_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(super_admin_required),
):
    property_obj = await db.get(Property, property_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")

    property_obj.status = PropertyStatus.LIVE
    property_obj.rejection_reason = None
    await db.commit()
    await AuditService.record(
        db,
        "property.approved",
        actor_user_id=current_admin.id,
        entity_type="property",
        entity_id=property_obj.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
    )

    return {"id": property_obj.id, "status": property_obj.status}


@router.post("/properties/{property_id}/reject")
async def reject_property(
    property_id: int,
    reason: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(super_admin_required),
):
    property_obj = await db.get(Property, property_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")

    property_obj.status = PropertyStatus.REJECTED
    property_obj.rejection_reason = reason
    await db.commit()
    await AuditService.record(
        db,
        "property.rejected",
        actor_user_id=current_admin.id,
        entity_type="property",
        entity_id=property_obj.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        metadata={"reason": reason},
    )

    return {"id": property_obj.id, "status": property_obj.status}
