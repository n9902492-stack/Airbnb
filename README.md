# Nestora

A modern property-rental marketplace inspired by the useful workflows of leading travel marketplaces, with an original UI and product structure.

## Stack
- Frontend: React + TypeScript + Vite
- Backend: Python + FastAPI
- API: REST
- Roles: Guest/User, Owner/Admin, Super Admin

## Panels
### User
Search stays, filter properties, view rich property details, save favourites, create bookings, view trips and profile.

### Owner/Admin
Create and edit listings, upload property details, manage pricing and availability, review reservations, see earnings and listing performance.

### Super Admin
Platform overview, user/owner management, listing moderation, booking oversight, reports, platform settings and audit visibility.

## Local development

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Backend
```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Frontend defaults to http://localhost:5173 and backend to http://localhost:8000.
