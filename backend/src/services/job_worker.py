import asyncio
import json

from src.core.config import settings
from src.db.session import AsyncSessionLocal
from src.services.booking_lifecycle_service import BookingLifecycleService
from src.services.payout_automation_service import PayoutAutomationService


async def handle_job(name: str, payload: dict) -> None:
    if name == "maintenance_tick":
        async with AsyncSessionLocal() as db:
            await BookingLifecycleService.expire_unpaid(db)
            await BookingLifecycleService.complete_finished_stays(db)
            await PayoutAutomationService.process_ready(db)


async def redis_worker_loop() -> None:
    if not settings.redis_url:
        while True:
            await handle_job("maintenance_tick", {})
            await asyncio.sleep(60)

    from redis.asyncio import Redis

    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        while True:
            item = await redis.brpop(settings.redis_job_queue, timeout=5)
            if not item:
                await handle_job("maintenance_tick", {})
                continue
            _, raw = item
            job = json.loads(raw)
            await handle_job(job.get("name", ""), job.get("payload") or {})
    finally:
        await redis.aclose()
