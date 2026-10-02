from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user
from src.db.session import get_db
from src.models.booking import Booking
from src.models.message import BookingMessage
from src.models.property import Property
from src.models.user import User


router = APIRouter()


class MessageCreate(BaseModel):
    body: str = Field(min_length=1, max_length=3000)


async def _authorized_booking(
    db: AsyncSession,
    booking_id: int,
    user: User,
) -> Booking:
    booking = await db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.guest_id == user.id:
        return booking

    property_obj = await db.get(Property, booking.property_id)
    if property_obj and property_obj.owner_id == user.id:
        return booking

    raise HTTPException(status_code=403, detail="You cannot access this conversation")


@router.get("/{booking_id}")
async def list_messages(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _authorized_booking(db, booking_id, current_user)
    result = await db.execute(
        select(BookingMessage, User.full_name)
        .join(User, User.id == BookingMessage.sender_id)
        .where(BookingMessage.booking_id == booking_id)
        .order_by(BookingMessage.created_at.asc())
    )
    return [
        {
            "id": message.id,
            "booking_id": message.booking_id,
            "sender_id": message.sender_id,
            "sender_name": sender_name,
            "body": message.body,
            "created_at": message.created_at,
        }
        for message, sender_name in result.all()
    ]


@router.post("/{booking_id}")
async def send_message(
    booking_id: int,
    payload: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _authorized_booking(db, booking_id, current_user)
    message = BookingMessage(
        booking_id=booking_id,
        sender_id=current_user.id,
        body=payload.body.strip(),
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return {
        "id": message.id,
        "booking_id": message.booking_id,
        "sender_id": message.sender_id,
        "sender_name": current_user.full_name,
        "body": message.body,
        "created_at": message.created_at,
    }
