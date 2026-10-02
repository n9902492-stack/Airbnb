# Nestora Backend Architecture

The backend uses a clean, feature-oriented FastAPI structure with PostgreSQL.

## Folder layout

```text
backend/
├── .env                  # Local secrets/config only. Never commit this file.
├── .env.example          # Safe configuration template.
├── requirements.txt
├── alembic.ini
├── docker-compose.yml
├── alembic/              # Database migrations
└── src/
    ├── main.py            # FastAPI application entry point
    ├── api/
    │   ├── deps.py        # Shared API dependencies / authorization
    │   ├── router.py      # Central API router
    │   └── routes/
    │       ├── auth.py
    │       ├── properties.py
    │       ├── bookings.py
    │       ├── reviews.py
    │       ├── transfers.py
    │       ├── owner.py
    │       └── super_admin.py
    ├── core/
    │   └── config.py      # Environment-driven application settings
    ├── db/
    │   ├── base.py        # SQLAlchemy declarative base
    │   ├── session.py     # PostgreSQL async session
    │   └── migrations/
    ├── models/            # SQLAlchemy database models only
    │   ├── user.py
    │   ├── property.py
    │   ├── booking.py
    │   ├── review.py
    │   ├── transfer.py
    │   └── verification_code.py
    ├── schemas/           # Pydantic request/response contracts
    │   ├── auth.py
    │   ├── user.py
    │   ├── property.py
    │   ├── booking.py
    │   ├── review.py
    │   ├── transfer.py
    │   └── verification.py
    └── services/          # Business logic
        ├── auth_service.py
        ├── property_service.py
        ├── booking_service.py
        ├── review_service.py
        ├── otp_service.py
        ├── email_service.py
        ├── image_service.py
        └── map_service.py
```

## Dependency direction

Routes should stay thin:

```text
API Route
  ↓
Schema validation
  ↓
Service
  ↓
SQLAlchemy model / PostgreSQL
```

Do not put SQL queries, password logic, pricing logic, or email logic directly inside React or route files.

## Environment setup

Create the private local environment file:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Only `.env.example` is committed. The real `.env` is ignored by Git.

## PostgreSQL

Start PostgreSQL through Docker:

```bash
docker compose up -d
```

Run migrations:

```bash
alembic upgrade head
```

Run FastAPI:

```bash
uvicorn src.main:app --reload --port 8000
```

## Coding rules

1. Database tables belong only in `src/models`.
2. Request/response DTOs belong only in `src/schemas`.
3. Reusable business logic belongs only in `src/services`.
4. HTTP endpoints belong only in `src/api/routes`.
5. PostgreSQL configuration and sessions belong only in `src/db`.
6. Secrets never belong in source files.
7. Frontend must communicate with backend through APIs; it must never access PostgreSQL directly.
8. User, owner, and super-admin permissions are enforced by the backend, not only by hidden frontend buttons.
