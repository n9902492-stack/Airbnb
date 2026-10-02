from decimal import Decimal

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.property import Property, PropertyStatus
from src.schemas.property import PropertyCreate, PropertyUpdate
from src.services.map_service import MapService


class PropertyService:
    @staticmethod
    async def list_live(
        db: AsyncSession,
        *,
        q: str | None = None,
        city: str | None = None,
        category: str | None = None,
        guests: int | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
    ) -> list[Property]:
        statement = select(Property).where(Property.status == PropertyStatus.LIVE)

        if q:
            like = f"%{q.strip()}%"
            statement = statement.where(
                or_(
                    Property.title.ilike(like),
                    Property.city.ilike(like),
                    Property.state.ilike(like),
                    Property.country.ilike(like),
                    Property.description.ilike(like),
                )
            )

        if city:
            statement = statement.where(Property.city.ilike(f"%{city.strip()}%"))
        if category:
            statement = statement.where(Property.category.ilike(category.strip()))
        if guests is not None:
            statement = statement.where(Property.guests >= guests)
        if min_price is not None:
            statement = statement.where(Property.price_per_night >= min_price)
        if max_price is not None:
            statement = statement.where(Property.price_per_night <= max_price)

        statement = statement.order_by(Property.created_at.desc())
        result = await db.execute(statement)
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
        data = payload.model_dump()

        if data.get("latitude") is None or data.get("longitude") is None:
            address_query = ", ".join(
                value
                for value in [
                    data.get("address_line"),
                    data.get("city"),
                    data.get("state"),
                    data.get("postal_code"),
                    data.get("country"),
                ]
                if value
            )
            try:
                places = await MapService.geocode(address_query)
                if places:
                    data["latitude"] = places[0]["latitude"]
                    data["longitude"] = places[0]["longitude"]
            except Exception:
                pass

        property_obj = Property(
            owner_id=owner_id,
            status=PropertyStatus.PENDING,
            **data,
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
