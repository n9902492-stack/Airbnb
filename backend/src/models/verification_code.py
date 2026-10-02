import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


class VerificationPurpose(str, enum.Enum):
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"


class VerificationCode(Base):
    __tablename__ = "verification_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    purpose: Mapped[VerificationPurpose] = mapped_column(
        Enum(VerificationPurpose, name="verification_purpose"),
        index=True,
        nullable=False,
    )
    code_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
