import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from src.api.router import api_router
from src.core.config import settings
from src.core.security_headers import SecurityHeadersMiddleware
from src.services.booking_expiry_worker import booking_expiry_loop


@asynccontextmanager
async def lifespan(_: FastAPI):
    expiry_task = asyncio.create_task(booking_expiry_loop())
    try:
        yield
    finally:
        expiry_task.cancel()
        try:
            await expiry_task
        except asyncio.CancelledError:
            pass


if settings.app_env == "production":
    if settings.secret_key == "change-this-in-your-local-env" or len(settings.secret_key) < 32:
        raise RuntimeError("Production SECRET_KEY must be replaced with a strong random value")
    if settings.payment_provider == "razorpay" and (
        not settings.razorpay_key_id or not settings.razorpay_key_secret
    ):
        raise RuntimeError("Razorpay is enabled but production credentials are missing")
    if settings.razorpay_route_enabled and settings.payment_provider != "razorpay":
        raise RuntimeError("Razorpay Route requires PAYMENT_PROVIDER=razorpay")
    if (
        settings.razorpay_route_enabled
        and settings.razorpay_route_webhook_required
        and not settings.razorpay_webhook_secret
    ):
        raise RuntimeError("Razorpay Route requires a webhook secret for reconciliation")

app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
    version="0.4.0",
    lifespan=lifespan,
)

app.add_middleware(SecurityHeadersMiddleware)

if settings.app_env == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[host.strip() for host in settings.allowed_hosts.split(",") if host.strip()],
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory="uploads", check_dir=False), name="uploads")
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["Health"])
async def health():
    return {
        "status": "ok",
        "environment": settings.app_env,
        "database": "postgresql",
        "payment_provider": settings.payment_provider,
    }
