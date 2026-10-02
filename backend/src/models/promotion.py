from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


class PromotionCode(Base):
    __tablename__ = "promotion_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    discount_type: Mapped[str] = mapped_column(String(20), nullable=False)  # percent | fixed
    discount_value: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    minimum_spend: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    max_uses: Mapped[int | None] = mapped_column(Integer, nullable=True)
    used_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
