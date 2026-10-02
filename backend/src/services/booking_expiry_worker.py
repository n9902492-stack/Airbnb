import asyncio

from src.db.session import AsyncSessionLocal
from src.services.booking_lifecycle_service import BookingLifecycleService


async def booking_expiry_loop() -> None:
    while True:
        try:
            async with AsyncSessionLocal() as db:
                await BookingLifecycleService.expire_unpaid(db)
        except Exception:
            pass

        await asyncio.sleep(60)
