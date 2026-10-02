import asyncio
import time
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from starlette.middleware.trustedhost import TrustedHostMiddleware

from src.api.router import api_router
from src.core.config import settings
from src.core.security_headers import SecurityHeadersMiddleware
from src.db.session import AsyncSessionLocal
from src.services.job_worker import redis_worker_loop


@asynccontextmanager
async def lifespan(_: FastAPI):
    worker = asyncio.create_task(redis_worker_loop()) if settings.job_worker_enabled else None
    try:
        yield
    finally:
        if worker:
            worker.cancel()
            try:
                await worker
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
    if settings.storage_provider == "s3" and not settings.s3_bucket:
        raise RuntimeError("S3 storage is enabled but S3_BUCKET is missing")

if settings.sentry_dsn:
    import sentry_sdk
    sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0.1)

app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
    version="0.5.0",
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


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or uuid4().hex
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception as exc:
        if settings.sentry_dsn:
            import sentry_sdk
            sentry_sdk.capture_exception(exc)
        response = JSONResponse(status_code=500, content={"detail": "Internal server error", "request_id": request_id})
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-Ms"] = f"{(time.perf_counter() - started) * 1000:.1f}"
    return response


if settings.storage_provider == "local":
    app.mount("/uploads", StaticFiles(directory="uploads", check_dir=False), name="uploads")

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health/live", tags=["Health"])
async def live():
    return {"status": "ok"}


@app.get("/health/ready", tags=["Health"])
async def ready():
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "ok"}
    except Exception:
        return JSONResponse(status_code=503, content={"status": "not_ready", "database": "error"})
