from pydantic import BaseModel, Field


class PayoutAccountUpdate(BaseModel):
    linked_account_id: str = Field(
        min_length=8,
        max_length=120,
        pattern=r"^acc_[A-Za-z0-9]+$",
    )
