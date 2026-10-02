from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import require_roles
from src.db.session import get_db
from src.models.promotion import PromotionCode
from src.models.user import User, UserRole


router = APIRouter()
admin_required = require_roles(UserRole.SUPER_ADMIN)


class PromotionCreate(BaseModel):
    code: str = Field(min_length=3, max_length=40)
    discount_type: str = Field(pattern="^(percent|fixed)$")
    discount_value: Decimal = Field(gt=0)
    minimum_spend: Decimal = Field(default=0, ge=0)
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    max_uses: int | None = Field(default=None, ge=1)


@router.get("")
async def list_promotions(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_required),
):
    result = await db.execute(
        select(PromotionCode).order_by(PromotionCode.created_at.desc())
    )
    return [
        {
            "id": x.id,
            "code": x.code,
            "discount_type": x.discount_type,
            "discount_value": float(x.discount_value),
            "minimum_spend": float(x.minimum_spend),
            "valid_from": x.valid_from,
            "valid_until": x.valid_until,
            "max_uses": x.max_uses,
            "used_count": x.used_count,
            "active": x.active,
        }
        for x in result.scalars().all()
    ]


@router.post("")
async def create_promotion(
    payload: PromotionCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_required),
):
    code = payload.code.strip().upper()
    existing = await db.scalar(
        select(PromotionCode.id).where(PromotionCode.code == code)
    )
    if existing:
        raise HTTPException(status_code=409, detail="Promotion code already exists")

    promo = PromotionCode(code=code, **payload.model_dump(exclude={"code"}))
    db.add(promo)
    await db.commit()
    await db.refresh(promo)
    return {"id": promo.id, "code": promo.code, "active": promo.active}


@router.post("/{promotion_id}/toggle")
async def toggle_promotion(
    promotion_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_required),
):
    promo = await db.get(PromotionCode, promotion_id)
    if not promo:
        raise HTTPException(status_code=404, detail="Promotion not found")
    promo.active = not promo.active
    await db.commit()
    return {"id": promo.id, "active": promo.active}
