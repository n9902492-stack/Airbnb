from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user, require_roles
from src.db.session import get_db
from src.models.credit import CreditLedger
from src.models.user import User, UserRole
from src.services.credit_service import CreditService


router = APIRouter()
admin_required = require_roles(UserRole.SUPER_ADMIN)


class RedeemCode(BaseModel):
    code: str = Field(min_length=6, max_length=80)


class IssueCredit(BaseModel):
    amount: Decimal = Field(gt=0)
    expires_at: datetime | None = None


@router.get("")
async def credit_account(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    balance = await CreditService.balance(db, current_user.id)
    result = await db.execute(
        select(CreditLedger)
        .where(CreditLedger.user_id == current_user.id)
        .order_by(CreditLedger.created_at.desc())
        .limit(100)
    )
    return {
        "balance": float(balance),
        "ledger": [
            {
                "id": x.id,
                "amount": float(x.amount),
                "entry_type": x.entry_type,
                "reference_type": x.reference_type,
                "reference_id": x.reference_id,
                "note": x.note,
                "created_at": x.created_at,
            }
            for x in result.scalars().all()
        ],
    }


@router.post("/redeem")
async def redeem_credit(
    payload: RedeemCode,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        balance = await CreditService.redeem(db, current_user.id, payload.code)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return {"balance": float(balance)}


@router.post("/admin/issue")
async def issue_credit(
    payload: IssueCredit,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_required),
):
    item, raw = await CreditService.issue_code(
        db, payload.amount, payload.expires_at
    )
    return {
        "id": item.id,
        "code": raw,
        "amount": float(item.amount),
        "expires_at": item.expires_at,
        "message": "This code is only returned once. Share it securely.",
    }
