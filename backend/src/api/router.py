from fastapi import APIRouter

from src.api.routes import auth, bookings, owner, properties, reviews, super_admin, transfers

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(properties.router, prefix="/properties", tags=["Properties"])
api_router.include_router(bookings.router, prefix="/bookings", tags=["Bookings"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["Reviews"])
api_router.include_router(transfers.router, prefix="/transfers", tags=["Transfers"])
api_router.include_router(owner.router, prefix="/owner", tags=["Owner"])
api_router.include_router(super_admin.router, prefix="/super-admin", tags=["Super Admin"])
