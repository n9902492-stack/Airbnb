from decimal import Decimal

from pydantic import BaseModel


class CheckoutPreview(BaseModel):
    booking_id: int
    stay_subtotal: Decimal
    service_fee: Decimal
    transfer_fee: Decimal
    gst_rate: Decimal
    gst_amount: Decimal
    grand_total: Decimal
    currency: str = "INR"


class PaymentRead(BaseModel):
    id: int
    booking_id: int
    amount: Decimal
    currency: str
    status: str


class PaymentSession(PaymentRead):
    provider: str
    razorpay_key_id: str | None = None
    provider_order_id: str | None = None
    amount_paise: int | None = None


class RazorpayVerifyRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class CancellationResult(BaseModel):
    booking_id: int
    status: str
    refund_amount: Decimal
    refund_percent: int
    message: str
