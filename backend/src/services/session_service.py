import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.models.session import AuthSession


def _hash_refresh(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class SessionService:
    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: int,
        user_agent: str | None,
        ip_address: str | None,
    ) -> tuple[AuthSession, str]:
        raw = secrets.token_urlsafe(48)
        session = AuthSession(
            user_id=user_id,
            refresh_token_hash=_hash_refresh(raw),
            user_agent=(user_agent or "")[:300] or None,
            ip_address=(ip_address or "")[:80] or None,
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=settings.refresh_token_expire_days),
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session, raw

    @staticmethod
    async def rotate(
        db: AsyncSession,
        refresh_token: str,
        user_agent: str | None,
        ip_address: str | None,
    ) -> tuple[AuthSession, str] | None:
        token_hash = _hash_refresh(refresh_token)
        session = await db.scalar(
            select(AuthSession).where(
                AuthSession.refresh_token_hash == token_hash,
                AuthSession.revoked.is_(False),
            )
        )
        now = datetime.now(timezone.utc)
        if not session or session.expires_at <= now:
            return None

        session.revoked = True
        session.last_used_at = now
        await db.commit()
        return await SessionService.create(
            db,
            session.user_id,
            user_agent,
            ip_address,
        )

    @staticmethod
    async def revoke(
        db: AsyncSession,
        refresh_token: str,
    ) -> None:
        token_hash = _hash_refresh(refresh_token)
        session = await db.scalar(
            select(AuthSession).where(
                AuthSession.refresh_token_hash == token_hash
            )
        )
        if session and not session.revoked:
            session.revoked = True
            session.last_used_at = datetime.now(timezone.utc)
            await db.commit()


    @staticmethod
    async def revoke_all(
        db: AsyncSession,
        user_id: int,
    ) -> None:
        from sqlalchemy import update

        await db.execute(
            update(AuthSession)
            .where(
                AuthSession.user_id == user_id,
                AuthSession.revoked.is_(False),
            )
            .values(revoked=True, last_used_at=datetime.now(timezone.utc))
        )
        await db.commit()
