from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user
from src.db.session import get_db
from src.models.booking import Booking, BookingStatus
from src.models.booking_participant import BookingParticipant
from src.models.user import User
from src.services.notification_service import NotificationService


router = APIRouter()


class ParticipantInvite(BaseModel):
    email: EmailStr


async def _guest_booking(
    db: AsyncSession,
    booking_id: int,
    current_user: User,
) -> Booking:
    booking = await db.get(Booking, booking_id)
    if not booking or booking.guest_id != current_user.id:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


@router.get("/{booking_id}")
async def list_participants(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = await db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    participant = await db.scalar(
        select(BookingParticipant).where(
            BookingParticipant.booking_id == booking_id,
            BookingParticipant.user_id == current_user.id,
        )
    )
    if booking.guest_id != current_user.id and not participant:
        raise HTTPException(status_code=403, detail="No access to this reservation")

    booker = await db.get(User, booking.guest_id)
    result = await db.execute(
        select(BookingParticipant, User)
        .join(User, User.id == BookingParticipant.user_id)
        .where(BookingParticipant.booking_id == booking_id)
        .order_by(BookingParticipant.created_at.asc())
    )
    items = [{
        "user_id": booker.id,
        "name": booker.full_name,
        "email": booker.email,
        "role": "booker",
    }] if booker else []
    items.extend(
        {
            "id": item.id,
            "user_id": user.id,
            "name": user.full_name,
            "email": user.email,
            "role": item.role,
        }
        for item, user in result.all()
    )
    return items


@router.post("/{booking_id}")
async def invite_participant(
    booking_id: int,
    payload: ParticipantInvite,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = await _guest_booking(db, booking_id, current_user)
    if booking.status not in {BookingStatus.PENDING, BookingStatus.CONFIRMED}:
        raise HTTPException(status_code=409, detail="Participants can only be invited to active reservations")

    user = await db.scalar(
        select(User).where(User.email == payload.email.strip().lower())
    )
    if not user:
        raise HTTPException(status_code=404, detail="Invitee must already have a Nestora account")
    if user.id == booking.guest_id:
        raise HTTPException(status_code=409, detail="This user is already the booker")

    existing = await db.scalar(
        select(BookingParticipant).where(
            BookingParticipant.booking_id == booking_id,
            BookingParticipant.user_id == user.id,
        )
    )
    if existing:
        return {"id": existing.id, "user_id": user.id, "role": existing.role}

    item = BookingParticipant(
        booking_id=booking_id,
        user_id=user.id,
        role="co_traveler",
        invited_by_user_id=current_user.id,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)

    await NotificationService.create(
        db,
        user.id,
        "trip_invitation",
        "You were added to a trip",
        f"{current_user.full_name} added you to booking #{booking.id}.",
    )
    return {"id": item.id, "user_id": user.id, "role": item.role}


@router.delete("/{booking_id}/{participant_id}")
async def remove_participant(
    booking_id: int,
    participant_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _guest_booking(db, booking_id, current_user)
    item = await db.get(BookingParticipant, participant_id)
    if item and item.booking_id == booking_id:
        await db.delete(item)
        await db.commit()
    return {"ok": True}
