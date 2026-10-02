from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.property import Property
from src.models.review import Review


class GuestFavoriteService:
    @staticmethod
    async def refresh(db: AsyncSession, property_id: int) -> bool:
        property_obj = await db.get(Property, property_id)
        if not property_obj:
            return False

        result = await db.execute(
            select(func.avg(Review.rating), func.count(Review.id))
            .where(Review.property_id == property_id)
        )
        average, count = result.one()
        # Nestora reliability badge: mature listings with consistently strong verified reviews.
        property_obj.guest_favorite = bool(
            int(count or 0) >= 5 and float(average or 0) >= 4.8
        )
        await db.commit()
        return property_obj.guest_favorite
