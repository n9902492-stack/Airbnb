from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user
from src.db.session import get_db
from src.models.host_profile import HostProfile
from src.models.property import Property, PropertyStatus
from src.models.review import Review
from src.models.user import User
from src.schemas.host import HostProfileUpdate


router = APIRouter()


@router.get("/{host_id}")
async def public_host_profile(
    host_id: int,
    db: AsyncSession = Depends(get_db),
):
    host = await db.get(User, host_id)
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")

    profile = await db.scalar(
        select(HostProfile).where(HostProfile.user_id == host_id)
    )
    listings = await db.scalar(
        select(func.count(Property.id)).where(
            Property.owner_id == host_id,
            Property.status == PropertyStatus.LIVE,
        )
    )
    rating = await db.scalar(
        select(func.avg(Review.rating))
        .join(Property, Review.property_id == Property.id)
        .where(Property.owner_id == host_id)
    )

    return {
        "id": host.id,
        "full_name": host.full_name,
        "joined_at": host.created_at,
        "bio": profile.bio if profile else None,
        "avatar_url": profile.avatar_url if profile else None,
        "languages": profile.languages if profile else [],
        "interests": profile.interests if profile else [],
        "work": profile.work if profile else None,
        "verified_identity": profile.verified_identity if profile else False,
        "response_rate": profile.response_rate if profile else 100,
        "response_time_label": profile.response_time_label if profile else "within an hour",
        "live_listings": listings or 0,
        "average_rating": round(float(rating or 0), 2),
    }


@router.put("/me/profile")
async def update_host_profile(
    payload: HostProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = await db.scalar(
        select(HostProfile).where(HostProfile.user_id == current_user.id)
    )
    if not profile:
        profile = HostProfile(user_id=current_user.id)
        db.add(profile)

    for key, value in payload.model_dump().items():
        setattr(profile, key, value)

    await db.commit()
    await db.refresh(profile)
    return {"ok": True, "host_id": current_user.id}
