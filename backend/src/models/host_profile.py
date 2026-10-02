from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base


class HostProfile(Base):
    __tablename__ = "host_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    languages: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    interests: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    work: Mapped[str | None] = mapped_column(String(180), nullable=True)
    verified_identity: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    response_rate: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    response_time_label: Mapped[str] = mapped_column(String(80), default="within an hour", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User")
