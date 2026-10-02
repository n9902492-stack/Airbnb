import json
from decimal import Decimal

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user
from src.core.config import settings
from src.db.session import get_db
from src.models.booking import Booking, BookingStatus
from src.models.payment import Payment
from src.models.transfer import TransferRequest
from src.models.user import User
from src.schemas.payment import CheckoutPreview, PaymentRead, PaymentSession, RazorpayVerifyRequest
from src.services.booking_lifecycle_service import BookingLifecycleService
from src.services.payment_service import PaymentService
from src.services.payout_automation_service import PayoutAutomationService
from src.services.razorpay_service import RazorpayService


router = APIRouter()


@router.get("/checkout/{booking_id}", response_model=CheckoutPreview)
async def checkout_preview(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await BookingLifecycleService.expire_unpaid(db)
    booking = await db.get(Booking, booking_id)
    if not booking or booking.guest_id != current_user.id:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status == BookingStatus.CANCELLED:
        raise HTTPException(status_code=409, detail="Booking is no longer active")

    transfer = await db.scalar(
        select(TransferRequest).where(TransferRequest.booking_id == booking.id)
    )
    transfer_fee = Decimal(str(transfer.estimated_fare)) if transfer else Decimal("0")

    return {
        "booking_id": booking.id,
        "stay_subtotal": booking.subtotal,
        "service_fee": booking.service_fee,
        "transfer_fee": transfer_fee,
        "grand_total": booking.total_amount + transfer_fee,
        "currency": "INR",
    }


@router.post("/checkout/{booking_id}", response_model=PaymentSession)
async def create_payment(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await BookingLifecycleService.expire_unpaid(db)
    booking = await db.get(Booking, booking_id)
    if not booking or booking.guest_id != current_user.id:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status == BookingStatus.CANCELLED:
        raise HTTPException(status_code=409, detail="Booking hold has expired or was cancelled")

    existing = await db.scalar(select(Payment).where(Payment.booking_id == booking.id))
    if existing:
        payment = existing
    else:
        transfer = await db.scalar(
            select(TransferRequest).where(TransferRequest.booking_id == booking.id)
        )
        transfer_fee = Decimal(str(transfer.estimated_fare)) if transfer else Decimal("0")
        try:
            payment = await PaymentService.create_for_booking(db, booking, transfer_fee)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Payment provider error: {exc}")

    return {
        "id": payment.id,
        "booking_id": payment.booking_id,
        "amount": payment.amount,
        "currency": payment.currency,
        "status": payment.status.value,
        "provider": payment.provider,
        "razorpay_key_id": settings.razorpay_key_id if payment.provider == "razorpay" else None,
        "provider_order_id": payment.provider_order_id,
        "amount_paise": int(Decimal(payment.amount) * 100) if payment.provider == "razorpay" else None,
    }


@router.post("/{payment_id}/verify-razorpay", response_model=PaymentRead)
async def verify_razorpay_payment(
    payment_id: int,
    payload: RazorpayVerifyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payment = await db.get(Payment, payment_id)
    if not payment or payment.provider != "razorpay":
        raise HTTPException(status_code=404, detail="Razorpay payment not found")

    booking = await db.get(Booking, payment.booking_id)
    if not booking or booking.guest_id != current_user.id:
        raise HTTPException(status_code=403, detail="Payment does not belong to you")

    if payment.provider_order_id != payload.razorpay_order_id:
        raise HTTPException(status_code=400, detail="Order ID mismatch")

    if not RazorpayService.verify_checkout_signature(
        payload.razorpay_order_id,
        payload.razorpay_payment_id,
        payload.razorpay_signature,
    ):
        raise HTTPException(status_code=400, detail="Invalid payment signature")

    payment = await PaymentService.mark_paid(
        db,
        payment,
        booking,
        provider_payment_id=payload.razorpay_payment_id,
    )
    return {
        "id": payment.id,
        "booking_id": payment.booking_id,
        "amount": payment.amount,
        "currency": payment.currency,
        "status": payment.status.value,
    }


@router.post("/{payment_id}/demo-confirm", response_model=PaymentRead)
async def demo_confirm_payment(
    payment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payment = await db.get(Payment, payment_id)
    if not payment or payment.provider != "manual_demo":
        raise HTTPException(status_code=404, detail="Demo payment not found")

    booking = await db.get(Booking, payment.booking_id)
    if not booking or booking.guest_id != current_user.id:
        raise HTTPException(status_code=403, detail="Payment does not belong to you")

    try:
        payment = await PaymentService.mark_paid(db, payment, booking)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    return {
        "id": payment.id,
        "booking_id": payment.booking_id,
        "amount": payment.amount,
        "currency": payment.currency,
        "status": payment.status.value,
    }


@router.post("/webhooks/razorpay")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(default=""),
    db: AsyncSession = Depends(get_db),
):
    raw_body = await request.body()
    if not RazorpayService.verify_webhook_signature(raw_body, x_razorpay_signature):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    event = json.loads(raw_body)
    event_name = event.get("event")
    payment_entity = (
        event.get("payload", {})
        .get("payment", {})
        .get("entity", {})
    )

    if event_name == "payment.captured":
        order_id = payment_entity.get("order_id")
        provider_payment_id = payment_entity.get("id")
        payment = await db.scalar(
            select(Payment).where(Payment.provider_order_id == order_id)
        )
        if payment:
            booking = await db.get(Booking, payment.booking_id)
            if booking:
                await PaymentService.mark_paid(
                    db,
                    payment,
                    booking,
                    provider_payment_id=provider_payment_id,
                )

    if event_name in {"transfer.created", "transfer.processed", "transfer.failed", "transfer.reversed", "transfer.updated"}:
        transfer_entity = (
            event.get("payload", {})
            .get("transfer", {})
            .get("entity", {})
        )
        if transfer_entity:
            await PayoutAutomationService.reconcile_transfer_event(
                db,
                transfer_entity,
            )

    if event_name in {"settlement.processed", "settlement.failed"}:
        settlement_entity = (
            event.get("payload", {})
            .get("settlement", {})
            .get("entity", {})
        )
        settlement_id = settlement_entity.get("id")
        if settlement_id:
            await PayoutAutomationService.reconcile_settlement(
                db,
                settlement_id,
            )

    return {"ok": True}
