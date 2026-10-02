from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user
from src.db.session import get_db
from src.models.booking import Booking
from src.models.message_automation import MessageTemplate, ScheduledMessage
from src.models.property import Property
from src.models.user import User


router = APIRouter()


class TemplateCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    body: str = Field(min_length=1, max_length=3000)


class ScheduledCreate(BaseModel):
    booking_id: int
    body: str = Field(min_length=1, max_length=3000)
    send_at: datetime


async def _is_host_for_booking(db: AsyncSession, booking_id: int, user_id: int) -> bool:
    booking = await db.get(Booking, booking_id)
    if not booking:
        return False
    property_obj = await db.get(Property, booking.property_id)
    return bool(property_obj and property_obj.owner_id == user_id)


@router.get("/templates")
async def templates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(MessageTemplate)
        .where(MessageTemplate.owner_user_id == current_user.id)
        .order_by(MessageTemplate.created_at.desc())
    )
    return [
        {"id": x.id, "title": x.title, "body": x.body}
        for x in result.scalars().all()
    ]


@router.post("/templates")
async def create_template(
    payload: TemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = MessageTemplate(
        owner_user_id=current_user.id,
        title=payload.title,
        body=payload.body,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return {"id": item.id, "title": item.title, "body": item.body}


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = await db.get(MessageTemplate, template_id)
    if item and item.owner_user_id == current_user.id:
        await db.delete(item)
        await db.commit()
    return {"ok": True}


@router.post("/scheduled")
async def schedule_message(
    payload: ScheduledCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.send_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=422, detail="Scheduled time must be in the future")
    if not await _is_host_for_booking(db, payload.booking_id, current_user.id):
        raise HTTPException(status_code=403, detail="Only the primary host can schedule messages")

    item = ScheduledMessage(
        booking_id=payload.booking_id,
        sender_id=current_user.id,
        body=payload.body,
        send_at=payload.send_at,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return {"id": item.id, "send_at": item.send_at}


@router.get("/scheduled")
async def scheduled_messages(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ScheduledMessage)
        .where(
            ScheduledMessage.sender_id == current_user.id,
            ScheduledMessage.sent_at.is_(None),
        )
        .order_by(ScheduledMessage.send_at.asc())
    )
    return [
        {
            "id": x.id,
            "booking_id": x.booking_id,
            "body": x.body,
            "send_at": x.send_at,
        }
        for x in result.scalars().all()
    ]
