# Nestora

A clean full-stack property rental marketplace with separate User, Owner/Admin, and Super Admin experiences.

## Tech stack
- Frontend: React + TypeScript + Vite
- Backend: Python + FastAPI
- Database: PostgreSQL
- ORM: SQLAlchemy async
- Migrations: Alembic
- Authentication: JWT
- Roles: user, owner, super_admin

## Clean project structure

```text
Airbnb/
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── App.tsx
│   │   ├── data.ts
│   │   ├── types.ts
│   │   ├── main.tsx
│   │   └── styles.css
│   ├── package.json
│   └── vite.config.ts
│
├── backend/
│   ├── .env.example
│   ├── .gitignore
│   ├── requirements.txt
│   ├── docker-compose.yml
│   ├── alembic.ini
│   └── src/
│       ├── main.py
│       ├── api/
│       │   ├── deps.py
│       │   ├── router.py
│       │   └── routes/
│       │       ├── auth.py
│       │       ├── properties.py
│       │       ├── bookings.py
│       │       ├── owner.py
│       │       └── super_admin.py
│       ├── core/
│       │   ├── config.py
│       │   └── security.py
│       ├── db/
│       │   ├── base.py
│       │   └── session.py
│       ├── models/
│       │   ├── user.py
│       │   ├── property.py
│       │   └── booking.py
│       ├── schemas/
│       │   ├── auth.py
│       │   ├── user.py
│       │   ├── property.py
│       │   └── booking.py
│       └── services/
│           ├── auth_service.py
│           ├── property_service.py
│           └── booking_service.py
└── README.md
```

## Environment

Do not commit real secrets. Create your local backend environment file:

```bash
cd backend
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Edit `backend/.env` with your PostgreSQL password and JWT secret.

## Start PostgreSQL

```bash
cd backend
docker compose up -d
```

Default local database:

```text
database: nestora
user: postgres
port: 5432
```

## Run backend

```bash
cd backend
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
```

API docs:

```text
http://localhost:8000/docs
```

## Run frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:5173
```

## Backend responsibility rule

- `api/routes`: HTTP endpoints only
- `services`: business logic
- `schemas`: request/response validation
- `models`: PostgreSQL tables
- `db`: database connection/session
- `core`: settings/security/shared infrastructure

This keeps route code small and makes the project easier to understand and extend.
