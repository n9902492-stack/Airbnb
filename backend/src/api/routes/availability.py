from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.schemas.availability import AvailabilityResponse
from src.services.availability_service import AvailabilityService


router = APIRouter()


@router.get("/properties/{property_id}", response_model=AvailabilityResponse)
async def property_availability(
    property_id: int,
    start: date = Query(default_factory=date.today),
    days: int = Query(default=180, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    end = start + timedelta(days=days)
    blocked = await AvailabilityService.blocked_dates(db, property_id, start, end)
    return {"property_id": property_id, "blocked_dates": blocked}
