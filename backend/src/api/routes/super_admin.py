from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import require_roles
from src.db.session import get_db
from src.models.booking import Booking
from src.models.property import Property, PropertyStatus
from src.models.user import User, UserRole


router = APIRouter()
super_admin_required = require_roles(UserRole.SUPER_ADMIN)


@router.get("/overview")
async def overview(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(super_admin_required),
):
    users = await db.scalar(select(func.count(User.id)))
    owners = await db.scalar(
        select(func.count(User.id)).where(User.role == UserRole.OWNER)
    )
    listings = await db.scalar(select(func.count(Property.id)))
    bookings = await db.scalar(select(func.count(Booking.id)))

    return {
        "users": users or 0,
        "owners": owners or 0,
        "listings": listings or 0,
        "bookings": bookings or 0,
    }


@router.post("/properties/{property_id}/approve")
async def approve_property(
    property_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(super_admin_required),
):
    property_obj = await db.get(Property, property_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")

    property_obj.status = PropertyStatus.LIVE
    property_obj.rejection_reason = None
    await db.commit()

    return {"id": property_obj.id, "status": property_obj.status}


@router.post("/properties/{property_id}/reject")
async def reject_property(
    property_id: int,
    reason: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(super_admin_required),
):
    property_obj = await db.get(Property, property_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")

    property_obj.status = PropertyStatus.REJECTED
    property_obj.rejection_reason = reason
    await db.commit()

    return {"id": property_obj.id, "status": property_obj.status}
