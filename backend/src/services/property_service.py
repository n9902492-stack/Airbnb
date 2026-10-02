from datetime import date
from decimal import Decimal

from sqlalchemy import and_, exists, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.availability_block import AvailabilityBlock
from src.models.booking import Booking, BookingStatus
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
        check_in: date | None = None,
        check_out: date | None = None,
        bedrooms: int | None = None,
        beds: int | None = None,
        bathrooms: int | None = None,
        property_type: str | None = None,
        instant_book: bool | None = None,
        guest_favorite: bool | None = None,
        amenities: list[str] | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        min_lat: float | None = None,
        max_lat: float | None = None,
        min_lng: float | None = None,
        max_lng: float | None = None,
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

        if check_in and check_out:
            if check_out <= check_in:
                return []
            booking_conflict = exists(
                select(Booking.id).where(
                    Booking.property_id == Property.id,
                    Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
                    Booking.check_in < check_out,
                    Booking.check_out > check_in,
                )
            )
            owner_block = exists(
                select(AvailabilityBlock.id).where(
                    AvailabilityBlock.property_id == Property.id,
                    AvailabilityBlock.start_date < check_out,
                    AvailabilityBlock.end_date > check_in,
                )
            )
            statement = statement.where(~booking_conflict, ~owner_block)
        if bedrooms is not None:
            statement = statement.where(Property.bedrooms >= bedrooms)
        if beds is not None:
            statement = statement.where(Property.beds >= beds)
        if bathrooms is not None:
            statement = statement.where(Property.bathrooms >= bathrooms)
        if property_type:
            statement = statement.where(Property.property_type.ilike(property_type.strip()))
        if instant_book is not None:
            statement = statement.where(
                Property.booking_mode == ("instant" if instant_book else "request")
            )
        if guest_favorite is not None:
            statement = statement.where(Property.guest_favorite == guest_favorite)
        if amenities:
            statement = statement.where(Property.amenities.contains(amenities))
        if min_price is not None:
            statement = statement.where(Property.price_per_night >= min_price)
        if max_price is not None:
            statement = statement.where(Property.price_per_night <= max_price)

        if min_lat is not None:
            statement = statement.where(Property.latitude >= min_lat)
        if max_lat is not None:
            statement = statement.where(Property.latitude <= max_lat)
        if min_lng is not None:
            statement = statement.where(Property.longitude >= min_lng)
        if max_lng is not None:
            statement = statement.where(Property.longitude <= max_lng)

        statement = statement.order_by(Property.guest_favorite.desc(), Property.created_at.desc())
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
