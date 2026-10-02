from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.cohost import PropertyCoHost
from src.models.property import Property
from src.models.user import User, UserRole


class CoHostService:
    @staticmethod
    async def permission_for(
        db: AsyncSession,
        property_obj: Property,
        user: User,
    ) -> str | None:
        if user.role == UserRole.SUPER_ADMIN or property_obj.owner_id == user.id:
            return "full"

        cohost = await db.scalar(
            select(PropertyCoHost).where(
                PropertyCoHost.property_id == property_obj.id,
                PropertyCoHost.user_id == user.id,
            )
        )
        return cohost.permission if cohost else None

    @classmethod
    async def require(
        cls,
        db: AsyncSession,
        property_obj: Property,
        user: User,
        allowed: set[str],
    ) -> str:
        permission = await cls.permission_for(db, property_obj, user)
        if permission not in allowed and permission != "full":
            raise PermissionError("You do not have co-host permission for this action")
        return permission or ""
