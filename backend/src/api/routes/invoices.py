from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user
from src.db.session import get_db
from src.models.booking import Booking
from src.models.invoice import Invoice
from src.models.user import User


router = APIRouter()


@router.get("/{booking_id}")
async def get_invoice(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = await db.get(Booking, booking_id)
    if not booking or booking.guest_id != current_user.id:
        raise HTTPException(status_code=404, detail="Invoice not found")

    invoice = await db.scalar(
        select(Invoice).where(Invoice.booking_id == booking_id)
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not issued yet")

    return {
        "invoice_number": invoice.invoice_number,
        "booking_id": invoice.booking_id,
        "taxable_amount": float(invoice.taxable_amount),
        "gst_rate": float(invoice.gst_rate),
        "gst_amount": float(invoice.gst_amount),
        "total_amount": float(invoice.total_amount),
        "currency": invoice.currency,
        "issued_at": invoice.issued_at,
    }
