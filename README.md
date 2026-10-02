# Nestora

Nestora is a full-stack property-rental marketplace with separate experiences for travellers, property owners, and the platform super admin.

## Technology

- Frontend: React + TypeScript + Vite
- Backend: Python + FastAPI
- Database: PostgreSQL
- ORM: SQLAlchemy 2
- Migrations: Alembic
- Authentication: JWT bearer tokens

## Clean project structure

```text
Airbnb/
├── frontend/
│   ├── src/
│   │   ├── api/              # HTTP client and API functions
│   │   ├── pages/            # React screens
│   │   ├── App.tsx
│   │   ├── data.ts           # temporary demo fallback data
│   │   ├── types.ts
│   │   └── styles.css
│   ├── .env.example
│   ├── package.json
│   └── vite.config.ts
│
├── backend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── routes/       # FastAPI route files
│   │   │   ├── deps.py       # auth/permission dependencies
│   │   │   └── router.py
│   │   ├── core/
│   │   │   ├── config.py     # environment settings
│   │   │   └── security.py   # password/JWT helpers
│   │   ├── db/
│   │   │   ├── migrations/   # Alembic migrations
│   │   │   ├── base.py
│   │   │   └── session.py
│   │   ├── models/           # SQLAlchemy PostgreSQL models
│   │   ├── schemas/          # request/response models
│   │   ├── services/         # business logic
│   │   └── main.py           # FastAPI app entry point
│   ├── .env.example
│   ├── alembic.ini
│   └── requirements.txt
│
├── compose.yaml               # local PostgreSQL
└── README.md
```

## Roles

### User
- Register and log in
- Browse live properties
- View detailed property information
- Create bookings
- Future: favourites, trips, reviews, chat and payments

### Owner/Admin
- Owner-only dashboard
- Create property listings
- Provide detailed property information
- Update owned listings
- Listings enter moderation before becoming live
- Future: calendar, pricing, reservation management and analytics

### Super Admin
- Platform-level dashboard
- View users, owners, listings and bookings
- Approve or reject property listings
- Future: user moderation, reports, refunds, fees and platform settings

## Environment setup

Never commit your real `.env`.

Copy:

```bash
cd backend
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Then edit `backend/.env` locally.

## Start PostgreSQL

From the repository root:

```bash
docker compose up -d postgres
```

Default local database:

```text
Database: nestora
Host: localhost
Port: 5432
User: postgres
Password: postgres
```

These values are for local development only.

## Backend setup

```bash
cd backend

python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run database migrations:

```bash
alembic upgrade head
```

Start FastAPI:

```bash
uvicorn src.main:app --reload --port 8000
```

API documentation:

```text
http://localhost:8000/docs
```

Health endpoint:

```text
http://localhost:8000/health
```

## Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:5173
```

## API structure

```text
/api/v1/auth/register
/api/v1/auth/login
/api/v1/auth/me

/api/v1/properties
/api/v1/properties/{property_id}

/api/v1/bookings

/api/v1/owner/overview
/api/v1/owner/properties
/api/v1/owner/properties/{property_id}

/api/v1/super-admin/overview
/api/v1/super-admin/properties/{property_id}/approve
/api/v1/super-admin/properties/{property_id}/reject
```

## Important development rule

Keep responsibilities separate:

- React UI stays inside `frontend/`.
- Python API code stays inside `backend/src/`.
- PostgreSQL connection and migration code stays inside `backend/src/db/`.
- SQLAlchemy table definitions stay inside `backend/src/models/`.
- Pydantic request/response objects stay inside `backend/src/schemas/`.
- Business logic stays inside `backend/src/services/`.
- FastAPI endpoints stay inside `backend/src/api/routes/`.
- Secrets stay only in local `backend/.env`.

This structure should be preserved as new features are added.
