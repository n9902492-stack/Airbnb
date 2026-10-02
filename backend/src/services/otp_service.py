import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.models.verification_code import VerificationCode, VerificationPurpose


class OtpService:
    @staticmethod
    def _hash(code: str) -> str:
        value = f"{code}:{settings.secret_key}".encode()
        return hashlib.sha256(value).hexdigest()

    @staticmethod
    def generate_code() -> str:
        return f"{secrets.randbelow(1_000_000):06d}"

    @classmethod
    async def create(
        cls,
        db: AsyncSession,
        user_id: int,
        purpose: VerificationPurpose,
    ) -> tuple[VerificationCode, str]:
        await db.execute(
            update(VerificationCode)
            .where(
                VerificationCode.user_id == user_id,
                VerificationCode.purpose == purpose,
                VerificationCode.used_at.is_(None),
            )
            .values(used_at=datetime.now(timezone.utc))
        )

        code = cls.generate_code()
        record = VerificationCode(
            user_id=user_id,
            purpose=purpose,
            code_hash=cls._hash(code),
            expires_at=datetime.now(timezone.utc)
            + timedelta(minutes=settings.otp_expire_minutes),
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return record, code

    @classmethod
    async def verify(
        cls,
        db: AsyncSession,
        user_id: int,
        purpose: VerificationPurpose,
        code: str,
    ) -> bool:
        result = await db.execute(
            select(VerificationCode)
            .where(
                VerificationCode.user_id == user_id,
                VerificationCode.purpose == purpose,
                VerificationCode.used_at.is_(None),
            )
            .order_by(VerificationCode.created_at.desc())
            .limit(1)
        )
        record = result.scalar_one_or_none()
        if not record:
            return False

        now = datetime.now(timezone.utc)
        if record.expires_at <= now or record.attempts >= settings.otp_max_attempts:
            return False

        record.attempts += 1
        if not secrets.compare_digest(record.code_hash, cls._hash(code)):
            await db.commit()
            return False

        record.used_at = now
        await db.commit()
        return True
