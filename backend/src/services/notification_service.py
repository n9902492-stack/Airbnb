from sqlalchemy.ext.asyncio import AsyncSession

from src.models.notification import Notification


class NotificationService:
    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: int,
        kind: str,
        title: str,
        message: str,
    ) -> Notification:
        item = Notification(
            user_id=user_id,
            kind=kind,
            title=title,
            message=message,
        )
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item
