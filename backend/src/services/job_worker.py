import asyncio
import json
import time

from src.core.config import settings
from src.db.session import AsyncSessionLocal
from src.services.booking_lifecycle_service import BookingLifecycleService
from src.services.email_service import EmailService
from src.services.payout_automation_service import PayoutAutomationService


async def handle_job(name: str, payload: dict) -> None:
    if name == "maintenance_tick":
        async with AsyncSessionLocal() as db:
            await BookingLifecycleService.expire_unpaid(db)
            await BookingLifecycleService.complete_finished_stays(db)
            await PayoutAutomationService.process_ready(db)
        return

    if name == "booking_confirmation_email":
        await EmailService.send_booking_confirmation(
            payload["email"],
            payload["property_title"],
            payload["check_in"],
            payload["check_out"],
            payload["amount"],
        )
        return

    if name == "cancellation_email":
        await EmailService.send_cancellation_receipt(
            payload["email"],
            payload["property_title"],
            payload["refund_amount"],
            int(payload["refund_percent"]),
        )


async def redis_worker_loop() -> None:
    if not settings.redis_url:
        while True:
            await handle_job("maintenance_tick", {})
            await asyncio.sleep(60)

    from redis.asyncio import Redis

    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    last_maintenance = 0.0

    try:
        while True:
            item = await redis.brpop(settings.redis_job_queue, timeout=5)
            if item:
                _, raw = item
                job = json.loads(raw)
                try:
                    await handle_job(job.get("name", ""), job.get("payload") or {})
                except Exception:
                    # Production monitoring captures worker failures at process level.
                    # Failed jobs remain visible through logs/Sentry and can be retried
                    # explicitly without blocking the API request that created them.
                    pass

            now = time.monotonic()
            if now - last_maintenance >= 60:
                await handle_job("maintenance_tick", {})
                last_maintenance = now
    finally:
        await redis.aclose()
