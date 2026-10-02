from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.models.auth_event import AuthEvent


class AuthSecurityService:
    @staticmethod
    async def record(
        db: AsyncSession,
        email: str,
        event_type: str,
        success: bool,
    ) -> None:
        db.add(
            AuthEvent(
                email=email.lower(),
                event_type=event_type,
                success=success,
            )
        )
        await db.commit()

    @staticmethod
    async def login_allowed(db: AsyncSession, email: str) -> bool:
        since = datetime.now(timezone.utc) - timedelta(
            minutes=settings.login_attempt_window_minutes
        )
        failures = await db.scalar(
            select(func.count(AuthEvent.id)).where(
                AuthEvent.email == email.lower(),
                AuthEvent.event_type == "login",
                AuthEvent.success.is_(False),
                AuthEvent.created_at >= since,
            )
        )
        return int(failures or 0) < settings.login_max_attempts

    @staticmethod
    async def otp_resend_allowed(db: AsyncSession, email: str) -> bool:
        since = datetime.now(timezone.utc) - timedelta(
            seconds=settings.otp_resend_cooldown_seconds
        )
        count = await db.scalar(
            select(func.count(AuthEvent.id)).where(
                AuthEvent.email == email.lower(),
                AuthEvent.event_type == "otp_resend",
                AuthEvent.created_at >= since,
            )
        )
        return int(count or 0) == 0
