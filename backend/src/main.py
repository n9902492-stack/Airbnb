import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.api.router import api_router
from src.core.config import settings
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


app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
    version="0.3.0",
    lifespan=lifespan,
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
