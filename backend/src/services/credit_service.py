import hashlib
import secrets
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.booking import Booking
from src.models.credit import CreditLedger, GiftCreditCode, UserCreditAccount


def _code_hash(code: str) -> str:
    return hashlib.sha256(code.strip().upper().encode()).hexdigest()


class CreditService:
    @staticmethod
    async def account(
        db: AsyncSession,
        user_id: int,
        *,
        lock: bool = False,
    ) -> UserCreditAccount:
        statement = select(UserCreditAccount).where(
            UserCreditAccount.user_id == user_id
        )
        if lock:
            statement = statement.with_for_update()
        account = await db.scalar(statement)
        if not account:
            account = UserCreditAccount(user_id=user_id, balance=Decimal("0"))
            db.add(account)
            await db.flush()
        return account

    @classmethod
    async def balance(cls, db: AsyncSession, user_id: int) -> Decimal:
        account = await cls.account(db, user_id)
        return Decimal(account.balance)

    @classmethod
    async def issue_code(
        cls,
        db: AsyncSession,
        amount: Decimal,
        expires_at: datetime | None,
    ) -> tuple[GiftCreditCode, str]:
        raw = "NEST-" + secrets.token_urlsafe(14).replace("_", "").replace("-", "").upper()
        item = GiftCreditCode(
            code_hash=_code_hash(raw),
            amount=amount,
            expires_at=expires_at,
        )
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item, raw

    @classmethod
    async def redeem(
        cls,
        db: AsyncSession,
        user_id: int,
        code: str,
    ) -> Decimal:
        item = await db.scalar(
            select(GiftCreditCode)
            .where(GiftCreditCode.code_hash == _code_hash(code))
            .with_for_update()
        )
        if not item:
            raise ValueError("Credit code is invalid")
        if item.redeemed_at:
            raise ValueError("Credit code has already been redeemed")
        now = datetime.now(timezone.utc)
        if item.expires_at and item.expires_at < now:
            raise ValueError("Credit code has expired")

        account = await cls.account(db, user_id, lock=True)
        account.balance = Decimal(account.balance) + Decimal(item.amount)
        item.redeemed_by_user_id = user_id
        item.redeemed_at = now
        db.add(
            CreditLedger(
                user_id=user_id,
                amount=item.amount,
                entry_type="credit",
                reference_type="gift_credit",
                reference_id=str(item.id),
                note="Redeemed Nestora credit code",
            )
        )
        await db.commit()
        return Decimal(account.balance)

    @classmethod
    async def apply_to_booking(
        cls,
        db: AsyncSession,
        booking: Booking,
        checkout_total: Decimal,
    ) -> Decimal:
        if Decimal(booking.credit_amount or 0) > 0:
            return Decimal(booking.credit_amount)

        account = await cls.account(db, booking.guest_id, lock=True)
        applied = min(Decimal(account.balance), checkout_total)
        if applied <= 0:
            return Decimal("0")

        account.balance = Decimal(account.balance) - applied
        booking.credit_amount = applied
        db.add(
            CreditLedger(
                user_id=booking.guest_id,
                amount=-applied,
                entry_type="debit",
                reference_type="booking",
                reference_id=str(booking.id),
                note="Applied to booking checkout",
            )
        )
        await db.commit()
        return applied

    @classmethod
    async def refund_booking_credit(
        cls,
        db: AsyncSession,
        booking: Booking,
        refund_percent: int,
    ) -> Decimal:
        original = Decimal(booking.credit_amount or 0)
        if original <= 0 or refund_percent <= 0:
            return Decimal("0")

        target = (
            original * Decimal(refund_percent) / Decimal("100")
        ).quantize(Decimal("0.01"))
        already = Decimal(booking.credit_refunded_amount or 0)
        amount = max(Decimal("0"), target - already)
        if amount <= 0:
            return Decimal("0")

        account = await cls.account(db, booking.guest_id, lock=True)
        account.balance = Decimal(account.balance) + amount
        booking.credit_refunded_amount = already + amount
        db.add(
            CreditLedger(
                user_id=booking.guest_id,
                amount=amount,
                entry_type="credit",
                reference_type="booking_refund",
                reference_id=str(booking.id),
                note=f"Booking credit refund ({refund_percent}%)",
            )
        )
        await db.commit()
        return amount
