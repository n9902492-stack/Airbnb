import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from src.models.user import UserRole


STRONG_PASSWORD_MESSAGE = (
    "Password must be at least 10 characters and include uppercase, lowercase, "
    "number, and special character."
)


class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    account_type: Literal["user", "owner"] = "user"

    @field_validator("password")
    @classmethod
    def validate_strong_password(cls, value: str) -> str:
        checks = [
            re.search(r"[A-Z]", value),
            re.search(r"[a-z]", value),
            re.search(r"\d", value),
            re.search(r"[^A-Za-z0-9]", value),
        ]
        if not all(checks):
            raise ValueError(STRONG_PASSWORD_MESSAGE)
        return value


class UserRead(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: UserRole
    is_active: bool
    is_verified: bool

    model_config = ConfigDict(from_attributes=True)
