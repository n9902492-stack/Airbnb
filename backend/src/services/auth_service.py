from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import hash_password, verify_password
from src.models.user import User, UserRole
from src.schemas.user import UserCreate


class AuthService:
    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> User | None:
        result = await db.execute(select(User).where(User.email == email.lower()))
        return result.scalar_one_or_none()

    @classmethod
    async def register(cls, db: AsyncSession, payload: UserCreate) -> User:
        role = UserRole.OWNER if payload.account_type == "owner" else UserRole.USER
        user = User(
            full_name=payload.full_name.strip(),
            email=payload.email.lower(),
            password_hash=hash_password(payload.password),
            role=role,
            is_active=False,
            is_verified=False,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @classmethod
    async def authenticate(
        cls,
        db: AsyncSession,
        email: str,
        password: str,
    ) -> User | None:
        user = await cls.get_by_email(db, email)
        if not user or not verify_password(password, user.password_hash):
            return None
        if not user.is_verified or not user.is_active:
            return None
        return user

    @staticmethod
    async def activate_verified_user(db: AsyncSession, user: User) -> User:
        user.is_verified = True
        user.is_active = True
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def change_password(db: AsyncSession, user: User, new_password: str) -> None:
        user.password_hash = hash_password(new_password)
        await db.commit()
