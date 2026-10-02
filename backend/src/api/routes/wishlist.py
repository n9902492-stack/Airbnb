from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user
from src.db.session import get_db
from src.models.property import Property, PropertyStatus
from src.models.user import User
from src.models.wishlist import WishlistItem


router = APIRouter()


@router.get("")
async def list_wishlist(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(WishlistItem, Property)
        .join(Property, WishlistItem.property_id == Property.id)
        .where(
            WishlistItem.user_id == current_user.id,
            Property.status == PropertyStatus.LIVE,
        )
        .order_by(WishlistItem.created_at.desc())
    )
    return [
        {
            "id": item.id,
            "property_id": property_obj.id,
            "title": property_obj.title,
            "city": property_obj.city,
            "state": property_obj.state,
            "price_per_night": float(property_obj.price_per_night),
            "image_urls": property_obj.image_urls,
        }
        for item, property_obj in result.all()
    ]


@router.post("/{property_id}")
async def add_wishlist(
    property_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    property_obj = await db.get(Property, property_id)
    if not property_obj or property_obj.status != PropertyStatus.LIVE:
        raise HTTPException(status_code=404, detail="Property not found")

    existing = await db.scalar(
        select(WishlistItem).where(
            WishlistItem.user_id == current_user.id,
            WishlistItem.property_id == property_id,
        )
    )
    if existing:
        return {"id": existing.id, "property_id": property_id}

    item = WishlistItem(user_id=current_user.id, property_id=property_id)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return {"id": item.id, "property_id": property_id}


@router.delete("/{property_id}")
async def remove_wishlist(
    property_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = await db.scalar(
        select(WishlistItem).where(
            WishlistItem.user_id == current_user.id,
            WishlistItem.property_id == property_id,
        )
    )
    if item:
        await db.delete(item)
        await db.commit()
    return {"ok": True}
