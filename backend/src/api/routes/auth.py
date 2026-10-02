from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user
from src.core.config import settings
from src.core.security import create_access_token
from src.db.session import get_db
from src.models.user import User
from src.models.verification_code import VerificationPurpose
from src.schemas.auth import RefreshResponse, TokenResponse
from src.schemas.user import UserCreate, UserRead
from src.schemas.verification import (
    ForgotPasswordRequest,
    ResendOtpRequest,
    ResetPasswordRequest,
    VerifyOtpRequest,
)
from src.services.auth_security_service import AuthSecurityService
from src.services.auth_service import AuthService
from src.services.email_service import EmailService
from src.services.otp_service import OtpService
from src.services.session_service import SessionService


router = APIRouter()


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=token,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path="/api/v1/auth",
    )


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await AuthService.get_by_email(db, payload.email)
    if existing and existing.is_verified:
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    if existing and not existing.is_verified:
        user = existing
    else:
        user = await AuthService.register(db, payload)

    _, otp = await OtpService.create(db, user.id, VerificationPurpose.EMAIL_VERIFICATION)
    await EmailService.send_otp(user.email, otp, VerificationPurpose.EMAIL_VERIFICATION.value)
    return user


@router.post("/verify-email")
async def verify_email(payload: VerifyOtpRequest, db: AsyncSession = Depends(get_db)):
    user = await AuthService.get_by_email(db, payload.email)
    if not user:
        raise HTTPException(status_code=404, detail="Account not found")

    valid = await OtpService.verify(
        db,
        user.id,
        VerificationPurpose.EMAIL_VERIFICATION,
        payload.otp,
    )
    if not valid:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    await AuthService.activate_verified_user(db, user)
    return {"message": "Email verified. You can now sign in."}


@router.post("/resend-verification-otp")
async def resend_verification_otp(
    payload: ResendOtpRequest,
    db: AsyncSession = Depends(get_db),
):
    if not await AuthSecurityService.otp_resend_allowed(db, payload.email):
        raise HTTPException(status_code=429, detail="Please wait before requesting another OTP")

    user = await AuthService.get_by_email(db, payload.email)
    if user and not user.is_verified:
        _, otp = await OtpService.create(db, user.id, VerificationPurpose.EMAIL_VERIFICATION)
        await EmailService.send_otp(user.email, otp, VerificationPurpose.EMAIL_VERIFICATION.value)
        await AuthSecurityService.record(db, payload.email, "otp_resend", True)
    return {"message": "If the account requires verification, a new OTP has been sent."}


@router.post("/login", response_model=TokenResponse)
async def login(
    response: Response,
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    if not await AuthSecurityService.login_allowed(db, form.username):
        raise HTTPException(status_code=429, detail="Too many failed login attempts. Try again later.")

    user = await AuthService.get_by_email(db, form.username)
    if user and not user.is_verified:
        raise HTTPException(status_code=403, detail="Verify your email before signing in")

    user = await AuthService.authenticate(db, form.username, form.password)
    if not user:
        await AuthSecurityService.record(db, form.username, "login", False)
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    await AuthSecurityService.record(db, form.username, "login", True)
    _, refresh = await SessionService.create(
        db,
        user.id,
        request.headers.get("user-agent"),
        request.client.host if request.client else None,
    )
    _set_refresh_cookie(response, refresh)
    return TokenResponse(access_token=create_access_token(str(user.id)))


@router.post("/refresh", response_model=RefreshResponse)
async def refresh(
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db),
    refresh_token: str | None = Cookie(default=None, alias=settings.refresh_cookie_name),
):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh session missing")

    rotated = await SessionService.rotate(
        db,
        refresh_token,
        request.headers.get("user-agent"),
        request.client.host if request.client else None,
    )
    if not rotated:
        response.delete_cookie(settings.refresh_cookie_name, path="/api/v1/auth")
        raise HTTPException(status_code=401, detail="Refresh session expired")

    session, raw = rotated
    _set_refresh_cookie(response, raw)
    return RefreshResponse(access_token=create_access_token(str(session.user_id)))


@router.post("/logout")
async def logout(
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_token: str | None = Cookie(default=None, alias=settings.refresh_cookie_name),
):
    if refresh_token:
        await SessionService.revoke(db, refresh_token)
    response.delete_cookie(settings.refresh_cookie_name, path="/api/v1/auth")
    return {"ok": True}


@router.post("/forgot-password")
async def forgot_password(
    payload: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    user = await AuthService.get_by_email(db, payload.email)
    if user and user.is_verified:
        _, otp = await OtpService.create(db, user.id, VerificationPurpose.PASSWORD_RESET)
        await EmailService.send_otp(user.email, otp, VerificationPurpose.PASSWORD_RESET.value)
    return {"message": "If this email is registered, a password reset OTP has been sent."}


@router.post("/reset-password")
async def reset_password(
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    UserCreate(full_name="Password Reset", email=payload.email, password=payload.new_password)

    user = await AuthService.get_by_email(db, payload.email)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid reset request")

    valid = await OtpService.verify(
        db,
        user.id,
        VerificationPurpose.PASSWORD_RESET,
        payload.otp,
    )
    if not valid:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    await AuthService.change_password(db, user, payload.new_password)
    await SessionService.revoke_all(db, user.id)
    return {"message": "Password changed successfully. All previous sessions were signed out."}


@router.get("/me", response_model=UserRead)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
