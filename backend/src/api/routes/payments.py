from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user
from src.db.session import get_db
from src.models.booking import Booking
from src.models.payment import Payment
from src.models.transfer import TransferRequest
from src.models.user import User
from src.schemas.payment import CheckoutPreview, PaymentRead
from src.services.payment_service import PaymentService


router = APIRouter()


@router.get("/checkout/{booking_id}", response_model=CheckoutPreview)
async def checkout_preview(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = await db.get(Booking, booking_id)
    if not booking or booking.guest_id != current_user.id:
        raise HTTPException(status_code=404, detail="Booking not found")

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


@router.post("/checkout/{booking_id}", response_model=PaymentRead)
async def create_payment(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = await db.get(Booking, booking_id)
    if not booking or booking.guest_id != current_user.id:
        raise HTTPException(status_code=404, detail="Booking not found")

    existing = await db.scalar(select(Payment).where(Payment.booking_id == booking.id))
    if existing:
        return {
            "id": existing.id,
            "booking_id": existing.booking_id,
            "amount": existing.amount,
            "currency": existing.currency,
            "status": existing.status.value,
        }

    transfer = await db.scalar(
        select(TransferRequest).where(TransferRequest.booking_id == booking.id)
    )
    transfer_fee = Decimal(str(transfer.estimated_fare)) if transfer else Decimal("0")
    payment = await PaymentService.create_for_booking(db, booking, transfer_fee)

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
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    booking = await db.get(Booking, payment.booking_id)
    if not booking or booking.guest_id != current_user.id:
        raise HTTPException(status_code=403, detail="Payment does not belong to you")

    payment = await PaymentService.mark_paid(db, payment, booking)
    return {
        "id": payment.id,
        "booking_id": payment.booking_id,
        "amount": payment.amount,
        "currency": payment.currency,
        "status": payment.status.value,
    }
