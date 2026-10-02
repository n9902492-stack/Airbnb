from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.schemas.property import PropertyRead
from src.services.property_service import PropertyService


router = APIRouter()


@router.get("", response_model=list[PropertyRead])
async def list_properties(db: AsyncSession = Depends(get_db)):
    return await PropertyService.list_live(db)


@router.get("/{property_id}", response_model=PropertyRead)
async def get_property(
    property_id: int,
    db: AsyncSession = Depends(get_db),
):
    property_obj = await PropertyService.get_by_id(db, property_id)
    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found",
        )
    return property_obj
