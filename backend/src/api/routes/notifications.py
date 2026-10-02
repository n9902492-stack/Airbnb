from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user
from src.db.session import get_db
from src.models.notification import Notification
from src.models.user import User


router = APIRouter()


@router.get("")
async def list_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
    )
    return [
        {
            "id": item.id,
            "kind": item.kind,
            "title": item.title,
            "message": item.message,
            "is_read": item.is_read,
            "created_at": item.created_at,
        }
        for item in result.scalars().all()
    ]


@router.post("/{notification_id}/read")
async def mark_read(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = await db.get(Notification, notification_id)
    if item and item.user_id == current_user.id:
        item.is_read = True
        await db.commit()
    return {"ok": True}
