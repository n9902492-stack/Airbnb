import hashlib
import hmac
from decimal import Decimal

import httpx

from src.core.config import settings


class RazorpayService:
    BASE_URL = "https://api.razorpay.com/v1"

    @staticmethod
    def configured() -> bool:
        return bool(settings.razorpay_key_id and settings.razorpay_key_secret)

    @classmethod
    async def create_order(cls, amount: Decimal, receipt: str) -> dict:
        if not cls.configured():
            raise ValueError("Razorpay is not configured")

        amount_paise = int((amount * 100).quantize(Decimal("1")))
        async with httpx.AsyncClient(
            auth=(settings.razorpay_key_id, settings.razorpay_key_secret),
            timeout=15,
        ) as client:
            response = await client.post(
                f"{cls.BASE_URL}/orders",
                json={
                    "amount": amount_paise,
                    "currency": "INR",
                    "receipt": receipt,
                    "payment_capture": 1,
                },
            )
            response.raise_for_status()
            return response.json()

    @staticmethod
    def verify_checkout_signature(
        order_id: str,
        payment_id: str,
        signature: str,
    ) -> bool:
        body = f"{order_id}|{payment_id}".encode()
        expected = hmac.new(
            settings.razorpay_key_secret.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    @staticmethod
    def verify_webhook_signature(raw_body: bytes, signature: str) -> bool:
        if not settings.razorpay_webhook_secret:
            return False
        expected = hmac.new(
            settings.razorpay_webhook_secret.encode(),
            raw_body,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    @classmethod
    async def refund_payment(cls, payment_id: str, amount: Decimal) -> dict:
        if not cls.configured():
            raise ValueError("Razorpay is not configured")

        amount_paise = int((amount * 100).quantize(Decimal("1")))
        async with httpx.AsyncClient(
            auth=(settings.razorpay_key_id, settings.razorpay_key_secret),
            timeout=15,
        ) as client:
            response = await client.post(
                f"{cls.BASE_URL}/payments/{payment_id}/refund",
                json={"amount": amount_paise},
            )
            response.raise_for_status()
            return response.json()
