from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.booking import Booking, BookingStatus
from src.models.review import Review
from src.models.user import User
from src.schemas.review import ReviewCreate


class ReviewService:
    @staticmethod
    async def list_for_property(db: AsyncSession, property_id: int):
        result = await db.execute(
            select(Review, User.full_name)
            .join(User, User.id == Review.guest_id)
            .where(Review.property_id == property_id)
            .order_by(Review.created_at.desc())
        )
        items = []
        for review, guest_name in result.all():
            items.append(
                {
                    "id": review.id,
                    "property_id": review.property_id,
                    "booking_id": review.booking_id,
                    "guest_id": review.guest_id,
                    "rating": review.rating,
                    "comment": review.comment,
                    "created_at": review.created_at,
                    "guest_name": guest_name,
                }
            )
        return items

    @staticmethod
    async def summary(db: AsyncSession, property_id: int) -> tuple[float, int]:
        result = await db.execute(
            select(func.avg(Review.rating), func.count(Review.id))
            .where(Review.property_id == property_id)
        )
        average, count = result.one()
        return round(float(average or 0), 2), int(count or 0)

    @staticmethod
    async def create(
        db: AsyncSession,
        guest_id: int,
        property_id: int,
        payload: ReviewCreate,
    ) -> Review:
        booking = await db.get(Booking, payload.booking_id)
        if (
            not booking
            or booking.guest_id != guest_id
            or booking.property_id != property_id
            or booking.status != BookingStatus.COMPLETED
        ):
            raise ValueError("Only completed stays can be reviewed")

        existing = await db.scalar(
            select(Review.id).where(Review.booking_id == payload.booking_id)
        )
        if existing:
            raise ValueError("This booking has already been reviewed")

        review = Review(
            property_id=property_id,
            booking_id=payload.booking_id,
            guest_id=guest_id,
            rating=payload.rating,
            comment=payload.comment.strip(),
        )
        db.add(review)
        await db.commit()
        await db.refresh(review)
        return review
