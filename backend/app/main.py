from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Nestora API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Property(BaseModel):
    id: int
    title: str
    location: str
    price_per_night: int
    rating: float
    owner_id: int
    status: str = "live"

PROPERTIES = [
    Property(id=1, title="Cedar Glass House", location="Manali, Himachal Pradesh", price_per_night=7200, rating=4.93, owner_id=101),
    Property(id=2, title="Palm Courtyard Villa", location="Assagao, Goa", price_per_night=9800, rating=4.88, owner_id=102),
    Property(id=3, title="Old Town Loft", location="Jaipur, Rajasthan", price_per_night=4600, rating=4.91, owner_id=103),
]

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/api/properties")
def list_properties():
    return PROPERTIES

@app.get("/api/properties/{property_id}")
def get_property(property_id: int):
    for property in PROPERTIES:
        if property.id == property_id:
            return property
    raise HTTPException(status_code=404, detail="Property not found")

@app.get("/api/owner/overview")
def owner_overview():
    return {
        "active_listings": 6,
        "upcoming_stays": 14,
        "monthly_revenue": 184200,
        "average_rating": 4.91,
    }

@app.get("/api/super-admin/overview")
def super_admin_overview():
    return {
        "users": 12480,
        "verified_owners": 1286,
        "live_listings": 3942,
        "open_reports": 18,
    }
