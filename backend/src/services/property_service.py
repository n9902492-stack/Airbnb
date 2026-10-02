from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.property import Property, PropertyStatus
from src.schemas.property import PropertyCreate, PropertyUpdate


class PropertyService:
    @staticmethod
    async def list_live(db: AsyncSession) -> list[Property]:
        result = await db.execute(
            select(Property)
            .where(Property.status == PropertyStatus.LIVE)
            .order_by(Property.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(db: AsyncSession, property_id: int) -> Property | None:
        return await db.get(Property, property_id)

    @staticmethod
    async def create_for_owner(
        db: AsyncSession,
        owner_id: int,
        payload: PropertyCreate,
    ) -> Property:
        property_obj = Property(
            owner_id=owner_id,
            status=PropertyStatus.PENDING,
            **payload.model_dump(),
        )
        db.add(property_obj)
        await db.commit()
        await db.refresh(property_obj)
        return property_obj

    @staticmethod
    async def update(
        db: AsyncSession,
        property_obj: Property,
        payload: PropertyUpdate,
    ) -> Property:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(property_obj, field, value)

        await db.commit()
        await db.refresh(property_obj)
        return property_obj
