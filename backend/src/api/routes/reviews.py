from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user
from src.db.session import get_db
from src.models.user import User
from src.schemas.review import ReviewCreate, ReviewRead, ReviewSummary
from src.services.review_service import ReviewService


router = APIRouter()


@router.get("/properties/{property_id}", response_model=ReviewSummary)
async def property_reviews(
    property_id: int,
    db: AsyncSession = Depends(get_db),
):
    average, count = await ReviewService.summary(db, property_id)
    reviews = await ReviewService.list_for_property(db, property_id)
    return {
        "average_rating": average,
        "review_count": count,
        "reviews": reviews,
    }


@router.post(
    "/properties/{property_id}",
    response_model=ReviewRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_review(
    property_id: int,
    payload: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        review = await ReviewService.create(
            db,
            current_user.id,
            property_id,
            payload,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {
        "id": review.id,
        "property_id": review.property_id,
        "booking_id": review.booking_id,
        "guest_id": review.guest_id,
        "rating": review.rating,
        "comment": review.comment,
        "created_at": review.created_at,
        "guest_name": current_user.full_name,
    }
