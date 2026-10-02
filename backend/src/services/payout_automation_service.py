from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.payment import Payment
from src.models.payout import OwnerPayout, PayoutStatus
from src.models.payout_account import OwnerPayoutAccount
from src.services.notification_service import NotificationService
from src.services.razorpay_route_service import RazorpayRouteService


class PayoutAutomationService:
    @staticmethod
    async def process_ready(db: AsyncSession) -> int:
        if not RazorpayRouteService.configured():
            return 0

        result = await db.execute(
            select(OwnerPayout)
            .where(
                OwnerPayout.status == PayoutStatus.READY,
                OwnerPayout.provider_reference.is_(None),
            )
            .order_by(OwnerPayout.created_at.asc())
            .limit(25)
        )
        payouts = list(result.scalars().all())
        processed = 0

        for payout in payouts:
            payout_account = await db.scalar(
                select(OwnerPayoutAccount).where(
                    OwnerPayoutAccount.owner_id == payout.owner_id,
                    OwnerPayoutAccount.status == "active",
                )
            )
            if not payout_account:
                continue

            payment = await db.scalar(
                select(Payment).where(Payment.booking_id == payout.booking_id)
            )
            if not payment or payment.provider != "razorpay" or not payment.provider_payment_id:
                continue

            payout.status = PayoutStatus.PROCESSING
            await db.commit()

            try:
                transfer = await RazorpayRouteService.create_transfer(
                    payment.provider_payment_id,
                    payout_account.linked_account_id,
                    payout.owner_amount,
                    payout.booking_id,
                    payout.id,
                )
            except Exception:
                payout.status = PayoutStatus.FAILED
                await db.commit()
                await NotificationService.create(
                    db,
                    payout.owner_id,
                    "payout_failed",
                    "Payout could not be sent",
                    f"Payout for booking #{payout.booking_id} could not be created. The platform will retry after review.",
                )
                continue

            payout.provider_reference = transfer.get("id")
            transfer_status = transfer.get("status") or transfer.get("transfer_status")

            if transfer_status == "processed":
                payout.status = PayoutStatus.PAID
                payout.paid_at = datetime.now(timezone.utc)
                await NotificationService.create(
                    db,
                    payout.owner_id,
                    "payout_paid",
                    "Payout sent",
                    f"₹{payout.owner_amount} for booking #{payout.booking_id} has been transferred through Razorpay Route.",
                )
            else:
                payout.status = PayoutStatus.PROCESSING

            await db.commit()
            processed += 1

        return processed

    @staticmethod
    async def reconcile_settlement(
        db: AsyncSession,
        settlement_id: str,
    ) -> int:
        transfers = await RazorpayRouteService.fetch_transfers_for_settlement(
            settlement_id
        )
        updated = 0

        for transfer in transfers:
            transfer_id = transfer.get("id")
            status = transfer.get("status") or transfer.get("transfer_status")
            if not transfer_id:
                continue

            payout = await db.scalar(
                select(OwnerPayout).where(
                    OwnerPayout.provider_reference == transfer_id
                )
            )
            if not payout:
                continue

            if status == "processed":
                payout.status = PayoutStatus.PAID
                payout.paid_at = payout.paid_at or datetime.now(timezone.utc)
            elif status in {"failed", "reversed", "partially_reversed"}:
                payout.status = PayoutStatus.FAILED
            else:
                payout.status = PayoutStatus.PROCESSING

            updated += 1

        if updated:
            await db.commit()
        return updated
