from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.schemas.property import PropertyRead
from src.services.property_service import PropertyService


router = APIRouter()


@router.get("", response_model=list[PropertyRead])
async def list_properties(
    q: str | None = Query(default=None, max_length=120),
    city: str | None = Query(default=None, max_length=120),
    category: str | None = Query(default=None, max_length=80),
    guests: int | None = Query(default=None, ge=1),
    min_price: Decimal | None = Query(default=None, ge=0),
    max_price: Decimal | None = Query(default=None, ge=0),
    db: AsyncSession = Depends(get_db),
):
    return await PropertyService.list_live(
        db,
        q=q,
        city=city,
        category=category,
        guests=guests,
        min_price=min_price,
        max_price=max_price,
    )


@router.get("/{property_id}", response_model=PropertyRead)
async def get_property(
    property_id: int,
    db: AsyncSession = Depends(get_db),
):
    property_obj = await PropertyService.get_by_id(db, property_id)
    if not property_obj or property_obj.status.value != "live":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found",
        )
    return property_obj
