import asyncio

from src.db.session import AsyncSessionLocal
from src.services.booking_lifecycle_service import BookingLifecycleService
from src.services.payout_automation_service import PayoutAutomationService


async def booking_expiry_loop() -> None:
    while True:
        try:
            async with AsyncSessionLocal() as db:
                await BookingLifecycleService.expire_unpaid(db)
                await BookingLifecycleService.complete_finished_stays(db)
                await PayoutAutomationService.process_ready(db)
        except Exception:
            pass

        await asyncio.sleep(60)
