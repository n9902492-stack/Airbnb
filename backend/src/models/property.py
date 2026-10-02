import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base


class PropertyStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"
    LIVE = "live"
    REJECTED = "rejected"
    PAUSED = "paused"


class Property(Base):
    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    title: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    property_type: Mapped[str] = mapped_column(String(80), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)

    address_line: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    state: Mapped[str] = mapped_column(String(120), nullable=False)
    country: Mapped[str] = mapped_column(String(120), default="India", nullable=False)
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    guests: Mapped[int] = mapped_column(Integer, nullable=False)
    bedrooms: Mapped[int] = mapped_column(Integer, nullable=False)
    beds: Mapped[int] = mapped_column(Integer, nullable=False)
    bathrooms: Mapped[int] = mapped_column(Integer, nullable=False)

    price_per_night: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    cleaning_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    weekend_price_per_night: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    minimum_stay_nights: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    maximum_stay_nights: Mapped[int | None] = mapped_column(Integer, nullable=True)

    amenities: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    house_rules: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    image_urls: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)

    check_in_time: Mapped[str] = mapped_column(String(20), default="14:00", nullable=False)
    check_out_time: Mapped[str] = mapped_column(String(20), default="11:00", nullable=False)
    booking_mode: Mapped[str] = mapped_column(String(30), default="instant", index=True, nullable=False)
    guest_favorite: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)

    status: Mapped[PropertyStatus] = mapped_column(
        Enum(PropertyStatus, name="property_status"),
        default=PropertyStatus.DRAFT,
        index=True,
        nullable=False,
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    owner = relationship("User", back_populates="properties")
    bookings = relationship("Booking", back_populates="property")
    review_entries = relationship("Review", back_populates="property", cascade="all, delete-orphan")
    transfer_requests = relationship("TransferRequest", back_populates="property", cascade="all, delete-orphan")
    availability_blocks = relationship("AvailabilityBlock", back_populates="property", cascade="all, delete-orphan")
    wishlist_items = relationship("WishlistItem", back_populates="property", cascade="all, delete-orphan")
    pricing_rules = relationship("PricingRule", back_populates="property", cascade="all, delete-orphan")
    cohosts = relationship("PropertyCoHost", cascade="all, delete-orphan")
