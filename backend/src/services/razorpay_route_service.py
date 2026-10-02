from decimal import Decimal

import httpx

from src.core.config import settings


class RazorpayRouteService:
    BASE_URL = "https://api.razorpay.com/v1"

    @staticmethod
    def configured() -> bool:
        return bool(
            settings.razorpay_route_enabled
            and settings.razorpay_key_id
            and settings.razorpay_key_secret
        )

    @classmethod
    async def create_transfer(
        cls,
        payment_id: str,
        linked_account_id: str,
        amount: Decimal,
        booking_id: int,
        payout_id: int,
    ) -> dict:
        if not cls.configured():
            raise ValueError("Razorpay Route is not configured")

        amount_paise = int((amount * 100).quantize(Decimal("1")))

        async with httpx.AsyncClient(
            auth=(settings.razorpay_key_id, settings.razorpay_key_secret),
            timeout=20,
        ) as client:
            response = await client.post(
                f"{cls.BASE_URL}/payments/{payment_id}/transfers",
                json={
                    "transfers": [
                        {
                            "account": linked_account_id,
                            "amount": amount_paise,
                            "currency": "INR",
                            "notes": {
                                "booking_id": str(booking_id),
                                "payout_id": str(payout_id),
                            },
                            "linked_account_notes": ["booking_id", "payout_id"],
                            "on_hold": False,
                        }
                    ]
                },
            )
            response.raise_for_status()
            data = response.json()

        if isinstance(data, dict) and "items" in data:
            items = data.get("items") or []
            if not items:
                raise ValueError("Razorpay Route returned no transfer")
            return items[0]

        if isinstance(data, list):
            if not data:
                raise ValueError("Razorpay Route returned no transfer")
            return data[0]

        return data

    @classmethod
    async def fetch_transfers_for_settlement(cls, settlement_id: str) -> list[dict]:
        if not cls.configured():
            return []

        async with httpx.AsyncClient(
            auth=(settings.razorpay_key_id, settings.razorpay_key_secret),
            timeout=20,
        ) as client:
            response = await client.get(
                f"{cls.BASE_URL}/transfers",
                params={"recipient_settlement_id": settlement_id},
            )
            response.raise_for_status()
            data = response.json()
            return list(data.get("items") or [])
