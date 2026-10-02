from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user, require_roles
from src.db.session import get_db
from src.models.booking import Booking
from src.models.identity_verification import IdentityVerification
from src.models.property import Property
from src.models.resolution_claim import ResolutionClaim
from src.models.support_case import SupportCase
from src.models.user import User, UserRole
from src.services.notification_service import NotificationService


router = APIRouter()
admin_required = require_roles(UserRole.SUPER_ADMIN)


class IdentityStart(BaseModel):
    document_type: str = Field(pattern="^(passport|driving_license|national_id|other)$")
    provider_reference: str | None = Field(default=None, max_length=180)


class SupportCreate(BaseModel):
    booking_id: int | None = None
    case_type: str = Field(pattern="^(reservation_issue|refund|safety|damage|account|other)$")
    subject: str = Field(min_length=3, max_length=180)
    description: str = Field(min_length=10, max_length=5000)
    priority: str = Field(default="normal", pattern="^(low|normal|high|urgent)$")


class SupportUpdate(BaseModel):
    status: str = Field(pattern="^(open|in_progress|waiting_user|resolved|closed)$")
    resolution: str | None = Field(default=None, max_length=5000)


class ClaimCreate(BaseModel):
    booking_id: int
    amount: Decimal = Field(gt=0)
    reason: str = Field(min_length=10, max_length=5000)
    evidence_urls: list[str] = []


class ClaimResponse(BaseModel):
    status: str = Field(pattern="^(accepted|declined)$")
    response_note: str | None = Field(default=None, max_length=3000)


@router.get("/identity")
async def identity_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = await db.scalar(
        select(IdentityVerification).where(
            IdentityVerification.user_id == current_user.id
        )
    )
    if not item:
        return {"status": "not_started", "verified": False}

    return {
        "status": item.status,
        "verified": item.status == "verified",
        "provider": item.provider,
        "document_type": item.document_type,
        "rejection_reason": item.rejection_reason,
        "submitted_at": item.submitted_at,
        "verified_at": item.verified_at,
    }


@router.post("/identity/start")
async def start_identity(
    payload: IdentityStart,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = await db.scalar(
        select(IdentityVerification).where(
            IdentityVerification.user_id == current_user.id
        )
    )
    if not item:
        item = IdentityVerification(user_id=current_user.id)
        db.add(item)

    item.status = "pending"
    item.document_type = payload.document_type
    item.provider_reference = payload.provider_reference
    item.submitted_at = datetime.now(timezone.utc)
    item.rejection_reason = None
    await db.commit()
    return {
        "status": item.status,
        "message": (
            "Verification submitted for review."
            if payload.provider_reference
            else "Verification started. Connect an approved identity provider before collecting real identity documents."
        ),
    }


@router.get("/admin/identity")
async def pending_identity(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_required),
):
    result = await db.execute(
        select(IdentityVerification, User)
        .join(User, User.id == IdentityVerification.user_id)
        .where(IdentityVerification.status == "pending")
        .order_by(IdentityVerification.submitted_at.asc())
    )
    return [
        {
            "id": item.id,
            "user_id": user.id,
            "name": user.full_name,
            "email": user.email,
            "document_type": item.document_type,
            "provider": item.provider,
            "provider_reference": item.provider_reference,
            "submitted_at": item.submitted_at,
        }
        for item, user in result.all()
    ]


@router.post("/admin/identity/{verification_id}/approve")
async def approve_identity(
    verification_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_required),
):
    item = await db.get(IdentityVerification, verification_id)
    if not item:
        raise HTTPException(status_code=404, detail="Verification not found")
    item.status = "verified"
    item.verified_at = datetime.now(timezone.utc)
    item.rejection_reason = None
    await db.commit()
    await NotificationService.create(
        db, item.user_id, "identity_verified", "Identity verified",
        "Your identity verification is complete."
    )
    return {"id": item.id, "status": item.status}


@router.post("/admin/identity/{verification_id}/reject")
async def reject_identity(
    verification_id: int,
    reason: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_required),
):
    item = await db.get(IdentityVerification, verification_id)
    if not item:
        raise HTTPException(status_code=404, detail="Verification not found")
    item.status = "rejected"
    item.rejection_reason = reason
    await db.commit()
    await NotificationService.create(
        db, item.user_id, "identity_rejected", "Identity verification needs attention",
        reason
    )
    return {"id": item.id, "status": item.status}


@router.post("/support")
async def create_support_case(
    payload: SupportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.booking_id:
        booking = await db.get(Booking, payload.booking_id)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
    item = SupportCase(
        reporter_id=current_user.id,
        **payload.model_dump(),
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return {"id": item.id, "status": item.status}


@router.get("/support/mine")
async def my_support_cases(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(SupportCase)
        .where(SupportCase.reporter_id == current_user.id)
        .order_by(SupportCase.created_at.desc())
    )
    return [
        {
            "id": x.id,
            "booking_id": x.booking_id,
            "case_type": x.case_type,
            "subject": x.subject,
            "description": x.description,
            "status": x.status,
            "priority": x.priority,
            "resolution": x.resolution,
            "created_at": x.created_at,
        }
        for x in result.scalars().all()
    ]


@router.get("/admin/support")
async def all_support_cases(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_required),
):
    result = await db.execute(
        select(SupportCase, User)
        .join(User, User.id == SupportCase.reporter_id)
        .order_by(SupportCase.created_at.desc())
        .limit(300)
    )
    return [
        {
            "id": x.id,
            "reporter_id": user.id,
            "reporter_name": user.full_name,
            "booking_id": x.booking_id,
            "case_type": x.case_type,
            "subject": x.subject,
            "status": x.status,
            "priority": x.priority,
            "created_at": x.created_at,
        }
        for x, user in result.all()
    ]


@router.patch("/admin/support/{case_id}")
async def update_support_case(
    case_id: int,
    payload: SupportUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(admin_required),
):
    item = await db.get(SupportCase, case_id)
    if not item:
        raise HTTPException(status_code=404, detail="Case not found")
    item.status = payload.status
    item.resolution = payload.resolution
    item.assigned_admin_id = current_admin.id
    await db.commit()
    await NotificationService.create(
        db, item.reporter_id, "support_case_updated", "Support case updated",
        f"Case #{item.id} is now {item.status}."
    )
    return {"id": item.id, "status": item.status}


@router.post("/claims")
async def create_claim(
    payload: ClaimCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = await db.get(Booking, payload.booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    property_obj = await db.get(Property, booking.property_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")

    participants = {booking.guest_id, property_obj.owner_id}
    if current_user.id not in participants:
        raise HTTPException(status_code=403, detail="Not part of this reservation")

    respondent = property_obj.owner_id if current_user.id == booking.guest_id else booking.guest_id
    claim = ResolutionClaim(
        booking_id=booking.id,
        claimant_id=current_user.id,
        respondent_id=respondent,
        amount=payload.amount,
        reason=payload.reason,
        evidence_urls="\n".join(payload.evidence_urls),
    )
    db.add(claim)
    await db.commit()
    await db.refresh(claim)
    await NotificationService.create(
        db, respondent, "resolution_claim", "New Resolution Center request",
        f"A ₹{claim.amount} request was opened for booking #{booking.id}."
    )
    return {"id": claim.id, "status": claim.status}


@router.get("/claims/mine")
async def my_claims(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ResolutionClaim)
        .where(
            (ResolutionClaim.claimant_id == current_user.id)
            | (ResolutionClaim.respondent_id == current_user.id)
        )
        .order_by(ResolutionClaim.created_at.desc())
    )
    return [
        {
            "id": x.id,
            "booking_id": x.booking_id,
            "claimant_id": x.claimant_id,
            "respondent_id": x.respondent_id,
            "amount": float(x.amount),
            "reason": x.reason,
            "evidence_urls": x.evidence_urls.splitlines() if x.evidence_urls else [],
            "status": x.status,
            "response_note": x.response_note,
            "created_at": x.created_at,
        }
        for x in result.scalars().all()
    ]


@router.post("/claims/{claim_id}/respond")
async def respond_claim(
    claim_id: int,
    payload: ClaimResponse,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    claim = await db.get(ResolutionClaim, claim_id)
    if not claim or claim.respondent_id != current_user.id:
        raise HTTPException(status_code=404, detail="Claim not found")
    claim.status = payload.status
    claim.response_note = payload.response_note
    await db.commit()
    await NotificationService.create(
        db, claim.claimant_id, "resolution_claim_updated", "Resolution request updated",
        f"Claim #{claim.id} was {claim.status}."
    )
    return {"id": claim.id, "status": claim.status}
