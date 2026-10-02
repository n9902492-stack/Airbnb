from decimal import Decimal

from pydantic import BaseModel


class CheckoutPreview(BaseModel):
    booking_id: int
    stay_subtotal: Decimal
    service_fee: Decimal
    transfer_fee: Decimal
    grand_total: Decimal
    currency: str = "INR"


class PaymentRead(BaseModel):
    id: int
    booking_id: int
    amount: Decimal
    currency: str
    status: str
