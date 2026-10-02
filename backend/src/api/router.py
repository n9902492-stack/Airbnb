from fastapi import APIRouter

from src.api.routes import auth, availability, bookings, collaboration, hosts, invoices, message_tools, messages, notifications, offerings, owner, payments, promotions, properties, reviews, super_admin, transfers, trust_support, wishlist

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(properties.router, prefix="/properties", tags=["Properties"])
api_router.include_router(hosts.router, prefix="/hosts", tags=["Hosts"])
api_router.include_router(offerings.router, prefix="/offerings", tags=["Services & Experiences"])
api_router.include_router(collaboration.router, prefix="/collaboration", tags=["Collaboration"])
api_router.include_router(promotions.router, prefix="/promotions", tags=["Promotions"])
api_router.include_router(trust_support.router, prefix="/trust", tags=["Trust & Support"])
api_router.include_router(message_tools.router, prefix="/message-tools", tags=["Message Tools"])
api_router.include_router(bookings.router, prefix="/bookings", tags=["Bookings"])
api_router.include_router(availability.router, prefix="/availability", tags=["Availability"])
api_router.include_router(payments.router, prefix="/payments", tags=["Payments"])
api_router.include_router(invoices.router, prefix="/invoices", tags=["Invoices"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["Reviews"])
api_router.include_router(transfers.router, prefix="/transfers", tags=["Transfers"])
api_router.include_router(wishlist.router, prefix="/wishlist", tags=["Wishlist"])
api_router.include_router(messages.router, prefix="/messages", tags=["Messages"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(owner.router, prefix="/owner", tags=["Owner"])
api_router.include_router(super_admin.router, prefix="/super-admin", tags=["Super Admin"])
