import secrets
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user, require_roles
from src.db.session import get_db
from src.models.booking import Booking, BookingStatus
from src.models.cohost import PropertyCoHost
from src.models.property import Property
from src.models.special_offer import SpecialOffer
from src.models.user import User, UserRole
from src.models.wishlist_collection import WishlistCollection, WishlistCollectionMember
from src.models.wishlist_collection_item import WishlistCollectionItem
from src.models.wishlist_vote import WishlistVote
from src.services.notification_service import NotificationService


router = APIRouter()
host_required = require_roles(UserRole.OWNER, UserRole.SUPER_ADMIN)


class CoHostCreate(BaseModel):
    email: EmailStr
    permission: str = Field(default="calendar", pattern="^(calendar|messages|full)$")


class CollectionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    proposed_start_date: str | None = None
    proposed_end_date: str | None = None
    guest_count: int | None = Field(default=None, ge=1, le=50)


class CollectionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    proposed_start_date: str | None = None
    proposed_end_date: str | None = None
    guest_count: int | None = Field(default=None, ge=1, le=50)


class CollectionItemNote(BaseModel):
    note: str | None = Field(default=None, max_length=2000)


class CollectionVote(BaseModel):
    value: int = Field(ge=-1, le=1)


class CollectionItemCreate(BaseModel):
    property_id: int
    note: str | None = Field(default=None, max_length=2000)


class SpecialOfferCreate(BaseModel):
    guest_id: int
    check_in: str
    check_out: str
    guest_count: int = Field(ge=1)
    total_price: Decimal = Field(gt=0)


@router.get("/properties/{property_id}/cohosts")
async def list_cohosts(
    property_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(host_required),
):
    property_obj = await db.get(Property, property_id)
    if not property_obj or (
        current_user.role != UserRole.SUPER_ADMIN
        and property_obj.owner_id != current_user.id
    ):
        raise HTTPException(status_code=404, detail="Property not found")

    result = await db.execute(
        select(PropertyCoHost, User)
        .join(User, User.id == PropertyCoHost.user_id)
        .where(PropertyCoHost.property_id == property_id)
    )
    return [
        {
            "id": item.id,
            "user_id": user.id,
            "name": user.full_name,
            "email": user.email,
            "permission": item.permission,
        }
        for item, user in result.all()
    ]


@router.post("/properties/{property_id}/cohosts")
async def add_cohost(
    property_id: int,
    payload: CoHostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(host_required),
):
    property_obj = await db.get(Property, property_id)
    if not property_obj or (
        current_user.role != UserRole.SUPER_ADMIN
        and property_obj.owner_id != current_user.id
    ):
        raise HTTPException(status_code=404, detail="Property not found")

    user = await db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user:
        raise HTTPException(status_code=404, detail="User must have a Nestora account")
    if user.id == property_obj.owner_id:
        raise HTTPException(status_code=409, detail="Owner is already the primary host")

    existing = await db.scalar(
        select(PropertyCoHost).where(
            PropertyCoHost.property_id == property_id,
            PropertyCoHost.user_id == user.id,
        )
    )
    if existing:
        existing.permission = payload.permission
        item = existing
    else:
        item = PropertyCoHost(
            property_id=property_id,
            user_id=user.id,
            permission=payload.permission,
        )
        db.add(item)

    await db.commit()
    await NotificationService.create(
        db,
        user.id,
        "cohost_added",
        "You were added as a co-host",
        f"You can now help manage {property_obj.title}.",
    )
    return {"id": item.id, "user_id": user.id, "permission": item.permission}


@router.delete("/properties/{property_id}/cohosts/{cohost_id}")
async def remove_cohost(
    property_id: int,
    cohost_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(host_required),
):
    property_obj = await db.get(Property, property_id)
    if not property_obj or (
        current_user.role != UserRole.SUPER_ADMIN
        and property_obj.owner_id != current_user.id
    ):
        raise HTTPException(status_code=404, detail="Property not found")
    item = await db.get(PropertyCoHost, cohost_id)
    if item and item.property_id == property_id:
        await db.delete(item)
        await db.commit()
    return {"ok": True}


@router.post("/wishlists")
async def create_collection(
    payload: CollectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from datetime import date
    collection = WishlistCollection(
        owner_user_id=current_user.id,
        name=payload.name,
        share_token=secrets.token_urlsafe(24),
        proposed_start_date=date.fromisoformat(payload.proposed_start_date) if payload.proposed_start_date else None,
        proposed_end_date=date.fromisoformat(payload.proposed_end_date) if payload.proposed_end_date else None,
        guest_count=payload.guest_count,
    )
    db.add(collection)
    await db.commit()
    await db.refresh(collection)
    return {
        "id": collection.id,
        "name": collection.name,
        "share_token": collection.share_token,
    }


@router.get("/wishlists")
async def list_collections(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    member_ids = select(WishlistCollectionMember.collection_id).where(
        WishlistCollectionMember.user_id == current_user.id
    )
    result = await db.execute(
        select(WishlistCollection).where(
            (WishlistCollection.owner_user_id == current_user.id)
            | (WishlistCollection.id.in_(member_ids))
        ).order_by(WishlistCollection.created_at.desc())
    )
    return [
        {
            "id": x.id,
            "name": x.name,
            "share_token": x.share_token if x.owner_user_id == current_user.id else None,
            "owner_user_id": x.owner_user_id,
            "proposed_start_date": x.proposed_start_date,
            "proposed_end_date": x.proposed_end_date,
            "guest_count": x.guest_count,
        }
        for x in result.scalars().all()
    ]


@router.post("/wishlists/{collection_id}/items")
async def add_collection_item(
    collection_id: int,
    payload: CollectionItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    collection = await db.get(WishlistCollection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Wishlist not found")

    member = await db.scalar(
        select(WishlistCollectionMember).where(
            WishlistCollectionMember.collection_id == collection_id,
            WishlistCollectionMember.user_id == current_user.id,
        )
    )
    if collection.owner_user_id != current_user.id and not member:
        raise HTTPException(status_code=403, detail="No access to this wishlist")

    property_obj = await db.get(Property, payload.property_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")

    existing = await db.scalar(
        select(WishlistCollectionItem).where(
            WishlistCollectionItem.collection_id == collection_id,
            WishlistCollectionItem.property_id == payload.property_id,
        )
    )
    if not existing:
        db.add(WishlistCollectionItem(
            collection_id=collection_id,
            property_id=payload.property_id,
            added_by_user_id=current_user.id,
            note=payload.note,
        ))
        await db.commit()
    return {"ok": True}


@router.post("/wishlists/join/{share_token}")
async def join_collection(
    share_token: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    collection = await db.scalar(
        select(WishlistCollection).where(WishlistCollection.share_token == share_token)
    )
    if not collection:
        raise HTTPException(status_code=404, detail="Shared wishlist not found")
    if collection.owner_user_id == current_user.id:
        return {"id": collection.id, "name": collection.name}

    existing = await db.scalar(
        select(WishlistCollectionMember).where(
            WishlistCollectionMember.collection_id == collection.id,
            WishlistCollectionMember.user_id == current_user.id,
        )
    )
    if not existing:
        db.add(WishlistCollectionMember(
            collection_id=collection.id,
            user_id=current_user.id,
            role="editor",
        ))
        await db.commit()
    return {"id": collection.id, "name": collection.name}


@router.post("/properties/{property_id}/special-offers")
async def create_special_offer(
    property_id: int,
    payload: SpecialOfferCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(host_required),
):
    property_obj = await db.get(Property, property_id)
    if not property_obj or (
        current_user.role != UserRole.SUPER_ADMIN
        and property_obj.owner_id != current_user.id
    ):
        raise HTTPException(status_code=404, detail="Property not found")

    from datetime import date
    check_in = date.fromisoformat(payload.check_in)
    check_out = date.fromisoformat(payload.check_out)
    if check_out <= check_in:
        raise HTTPException(status_code=422, detail="Invalid dates")

    offer = SpecialOffer(
        property_id=property_id,
        owner_id=property_obj.owner_id,
        guest_id=payload.guest_id,
        check_in=check_in,
        check_out=check_out,
        guest_count=payload.guest_count,
        total_price=payload.total_price,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db.add(offer)
    await db.commit()
    await db.refresh(offer)
    await NotificationService.create(
        db,
        payload.guest_id,
        "special_offer",
        "You received a special offer",
        f"{property_obj.title} is available for ₹{offer.total_price}.",
    )
    return {"id": offer.id, "status": offer.status, "expires_at": offer.expires_at}


@router.get("/special-offers/mine")
async def my_special_offers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(SpecialOffer, Property)
        .join(Property, Property.id == SpecialOffer.property_id)
        .where(SpecialOffer.guest_id == current_user.id)
        .order_by(SpecialOffer.created_at.desc())
    )
    return [
        {
            "id": offer.id,
            "property_id": property_obj.id,
            "property_title": property_obj.title,
            "check_in": offer.check_in,
            "check_out": offer.check_out,
            "guest_count": offer.guest_count,
            "total_price": float(offer.total_price),
            "status": offer.status,
            "expires_at": offer.expires_at,
        }
        for offer, property_obj in result.all()
    ]


@router.post("/special-offers/{offer_id}/accept")
async def accept_special_offer(
    offer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    offer = await db.get(SpecialOffer, offer_id)
    if not offer or offer.guest_id != current_user.id:
        raise HTTPException(status_code=404, detail="Offer not found")
    if offer.status != "pending" or offer.expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=409, detail="Offer is no longer active")

    from src.services.availability_service import AvailabilityService
    available = await AvailabilityService.is_available(
        db, offer.property_id, offer.check_in, offer.check_out
    )
    if not available:
        offer.status = "expired"
        await db.commit()
        raise HTTPException(status_code=409, detail="Dates are no longer available")

    service_fee = (Decimal(offer.total_price) * Decimal("0.10")).quantize(Decimal("0.01"))
    booking = Booking(
        property_id=offer.property_id,
        guest_id=current_user.id,
        check_in=offer.check_in,
        check_out=offer.check_out,
        guest_count=offer.guest_count,
        subtotal=offer.total_price,
        service_fee=service_fee,
        total_amount=Decimal(offer.total_price) + service_fee,
        status=BookingStatus.PENDING,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
    )
    db.add(booking)
    offer.status = "accepted"
    await db.commit()
    await db.refresh(booking)
    return {"booking_id": booking.id, "status": booking.status.value}


async def _collection_access(
    db: AsyncSession,
    collection_id: int,
    user_id: int,
) -> WishlistCollection:
    collection = await db.get(WishlistCollection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Wishlist not found")
    if collection.owner_user_id == user_id:
        return collection
    member = await db.scalar(
        select(WishlistCollectionMember).where(
            WishlistCollectionMember.collection_id == collection_id,
            WishlistCollectionMember.user_id == user_id,
        )
    )
    if not member:
        raise HTTPException(status_code=403, detail="No access to this wishlist")
    return collection


@router.patch("/wishlists/{collection_id}")
async def update_collection(
    collection_id: int,
    payload: CollectionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from datetime import date
    collection = await _collection_access(db, collection_id, current_user.id)
    data = payload.model_dump(exclude_unset=True)
    if "proposed_start_date" in data:
        raw_start = data.pop("proposed_start_date")
        collection.proposed_start_date = date.fromisoformat(raw_start) if raw_start else None
    if "proposed_end_date" in data:
        raw_end = data.pop("proposed_end_date")
        collection.proposed_end_date = date.fromisoformat(raw_end) if raw_end else None
    for key, value in data.items():
        setattr(collection, key, value)
    await db.commit()
    return {"ok": True}


@router.get("/wishlists/{collection_id}")
async def collection_detail(
    collection_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    collection = await _collection_access(db, collection_id, current_user.id)
    result = await db.execute(
        select(WishlistCollectionItem, Property)
        .join(Property, Property.id == WishlistCollectionItem.property_id)
        .where(WishlistCollectionItem.collection_id == collection_id)
        .order_by(WishlistCollectionItem.created_at.desc())
    )
    items = []
    for item, property_obj in result.all():
        votes = await db.execute(
            select(WishlistVote.value).where(WishlistVote.item_id == item.id)
        )
        values = list(votes.scalars().all())
        items.append({
            "id": item.id,
            "property_id": property_obj.id,
            "title": property_obj.title,
            "city": property_obj.city,
            "state": property_obj.state,
            "image_urls": property_obj.image_urls,
            "price_per_night": float(property_obj.price_per_night),
            "note": item.note,
            "vote_score": sum(values),
        })
    return {
        "id": collection.id,
        "name": collection.name,
        "proposed_start_date": collection.proposed_start_date,
        "proposed_end_date": collection.proposed_end_date,
        "guest_count": collection.guest_count,
        "items": items,
    }


@router.patch("/wishlists/{collection_id}/items/{item_id}/note")
async def update_collection_note(
    collection_id: int,
    item_id: int,
    payload: CollectionItemNote,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _collection_access(db, collection_id, current_user.id)
    item = await db.get(WishlistCollectionItem, item_id)
    if not item or item.collection_id != collection_id:
        raise HTTPException(status_code=404, detail="Wishlist item not found")
    item.note = payload.note
    await db.commit()
    return {"ok": True}


@router.post("/wishlists/{collection_id}/items/{item_id}/vote")
async def vote_collection_item(
    collection_id: int,
    item_id: int,
    payload: CollectionVote,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _collection_access(db, collection_id, current_user.id)
    item = await db.get(WishlistCollectionItem, item_id)
    if not item or item.collection_id != collection_id:
        raise HTTPException(status_code=404, detail="Wishlist item not found")
    vote = await db.scalar(
        select(WishlistVote).where(
            WishlistVote.item_id == item_id,
            WishlistVote.user_id == current_user.id,
        )
    )
    if payload.value == 0:
        if vote:
            await db.delete(vote)
    elif vote:
        vote.value = payload.value
    else:
        db.add(WishlistVote(item_id=item_id, user_id=current_user.id, value=payload.value))
    await db.commit()
    return {"ok": True}
