from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user
from src.db.session import get_db
from src.models.booking import Booking
from src.models.message import BookingMessage
from src.models.property import Property
from src.services.cohost_service import CoHostService
from src.models.user import User
from src.services.image_service import ImageService
from src.services.notification_service import NotificationService


router = APIRouter()


class MessageCreate(BaseModel):
    body: str = Field(default="", max_length=3000)
    attachment_url: str | None = Field(default=None, max_length=600)


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
    if property_obj:
        permission = await CoHostService.permission_for(db, property_obj, user)
        if permission in {"messages", "full"}:
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
            "attachment_url": message.attachment_url,
            "read_at": message.read_at,
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
    booking = await _authorized_booking(db, booking_id, current_user)
    if not payload.body.strip() and not payload.attachment_url:
        raise HTTPException(status_code=422, detail="Message or attachment is required")
    message = BookingMessage(
        booking_id=booking_id,
        sender_id=current_user.id,
        body=payload.body.strip(),
        attachment_url=payload.attachment_url,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)

    property_obj = await db.get(Property, booking.property_id)
    recipient_id = (
        property_obj.owner_id
        if current_user.id == booking.guest_id and property_obj
        else booking.guest_id
    )
    if recipient_id and recipient_id != current_user.id:
        await NotificationService.create(
            db,
            recipient_id,
            "new_message",
            "New booking message",
            f"{current_user.full_name} sent a message about booking #{booking.id}.",
        )

    return {
        "id": message.id,
        "booking_id": message.booking_id,
        "sender_id": message.sender_id,
        "sender_name": current_user.full_name,
        "body": message.body,
        "attachment_url": message.attachment_url,
        "read_at": message.read_at,
        "created_at": message.created_at,
    }


@router.post("/uploads/image")
async def upload_message_image(
    file: UploadFile = File(...),
    _: User = Depends(get_current_user),
):
    try:
        url = await ImageService.save_property_image(file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"url": url}


@router.post("/{booking_id}/read")
async def mark_messages_read(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _authorized_booking(db, booking_id, current_user)
    result = await db.execute(
        select(BookingMessage).where(
            BookingMessage.booking_id == booking_id,
            BookingMessage.sender_id != current_user.id,
            BookingMessage.read_at.is_(None),
        )
    )
    items = list(result.scalars().all())
    now = datetime.now(timezone.utc)
    for item in items:
        item.read_at = now
    if items:
        await db.commit()
    return {"updated": len(items)}
