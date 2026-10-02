import aiosmtplib
from email.message import EmailMessage

from src.core.config import settings


class EmailService:
    @staticmethod
    async def send_otp(email: str, otp: str, purpose: str) -> None:
        if settings.app_env == "development" and not settings.smtp_host:
            print(f"[DEV OTP] {purpose} for {email}: {otp}")
            return

        subject = (
            "Verify your Nestora email"
            if purpose == "email_verification"
            else "Reset your Nestora password"
        )

        message = EmailMessage()
        message["From"] = settings.smtp_from_email
        message["To"] = email
        message["Subject"] = subject
        message.set_content(
            f"Your Nestora verification code is {otp}. "
            f"It expires in {settings.otp_expire_minutes} minutes. "
            "Do not share this code with anyone."
        )

        await aiosmtplib.send(
            message,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_username or None,
            password=settings.smtp_password or None,
            start_tls=settings.smtp_use_tls,
        )
