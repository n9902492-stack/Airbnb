import aiosmtplib
from email.message import EmailMessage

from src.core.config import settings


class EmailService:
    @staticmethod
    async def _send(email: str, subject: str, body: str) -> None:
        if settings.app_env == "development" and not settings.smtp_host:
            print(f"[DEV EMAIL] to={email} subject={subject}\n{body}")
            return

        message = EmailMessage()
        message["From"] = settings.smtp_from_email
        message["To"] = email
        message["Subject"] = subject
        message.set_content(body)

        await aiosmtplib.send(
            message,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_username or None,
            password=settings.smtp_password or None,
            start_tls=settings.smtp_use_tls,
        )

    @classmethod
    async def send_otp(cls, email: str, otp: str, purpose: str) -> None:
        subject = (
            "Verify your Nestora email"
            if purpose == "email_verification"
            else "Reset your Nestora password"
        )
        await cls._send(
            email,
            subject,
            (
                f"Your Nestora verification code is {otp}. "
                f"It expires in {settings.otp_expire_minutes} minutes. "
                "Do not share this code with anyone."
            ),
        )

    @classmethod
    async def send_booking_confirmation(
        cls,
        email: str,
        property_title: str,
        check_in: str,
        check_out: str,
        amount: str,
    ) -> None:
        await cls._send(
            email,
            "Your Nestora booking is confirmed",
            (
                f"Your reservation for {property_title} is confirmed.\n\n"
                f"Check-in: {check_in}\n"
                f"Check-out: {check_out}\n"
                f"Paid amount: ₹{amount}\n\n"
                "You can view the booking in My Trips."
            ),
        )

    @classmethod
    async def send_cancellation_receipt(
        cls,
        email: str,
        property_title: str,
        refund_amount: str,
        refund_percent: int,
    ) -> None:
        await cls._send(
            email,
            "Your Nestora booking was cancelled",
            (
                f"Your reservation for {property_title} was cancelled.\n\n"
                f"Refund: ₹{refund_amount} ({refund_percent}%)\n\n"
                "Refund timing depends on the payment provider and bank."
            ),
        )
