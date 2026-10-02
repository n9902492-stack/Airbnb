# Nestora Project Structure

The repository is organized so frontend, backend, environment configuration, and PostgreSQL code are easy to identify.

```text
Airbnb/
├── frontend/                       # React + TypeScript only
│   ├── .env                        # Local frontend config; never commit
│   ├── .env.example
│   ├── package.json
│   ├── vite.config.ts
│   ├── ARCHITECTURE.md
│   └── src/
│       ├── api/                    # Typed HTTP/domain API clients
│       │   ├── client.ts           # Shared request/token/upload layer
│       │   ├── auth.ts
│       │   ├── bookings.ts
│       │   └── property.ts
│       ├── components/             # Shared React components
│       ├── pages/                  # Route-level screens
│       ├── lib/                    # Compatibility/helpers
│       ├── App.tsx
│       └── main.tsx
│
├── backend/                        # Python + FastAPI only
│   ├── .env                        # Backend secrets + PostgreSQL config
│   ├── .env.example
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/                    # Versioned PostgreSQL migrations
│   ├── docker-compose.yml
│   ├── ARCHITECTURE.md
│   └── src/
│       ├── main.py                 # FastAPI entry point
│       ├── api/
│       │   ├── deps.py
│       │   ├── router.py
│       │   └── routes/             # HTTP endpoints
│       ├── core/                   # Settings/security
│       ├── db/                     # DB engine/session helpers
│       ├── models/                 # SQLAlchemy PostgreSQL tables
│       ├── schemas/                # Pydantic request/response contracts
│       └── services/               # Business logic
│
├── docs/
├── compose.yaml
├── .gitignore
├── PROJECT_STRUCTURE.md
└── README.md
```

## Where each kind of code belongs

| Work | Location |
|---|---|
| React page | `frontend/src/pages/` |
| Reusable React component | `frontend/src/components/` |
| Frontend API code | `frontend/src/api/` |
| FastAPI route | `backend/src/api/routes/` |
| Backend business logic | `backend/src/services/` |
| PostgreSQL table/model | `backend/src/models/` |
| Request/response schema | `backend/src/schemas/` |
| DB session/engine helper | `backend/src/db/` |
| Database migration | `backend/alembic/versions/` |
| Backend local environment | `backend/.env` |
| Frontend local environment | `frontend/.env` |

## Separation rules

- React never connects directly to PostgreSQL.
- Routes should stay small and call service functions.
- Services contain business rules.
- Models contain database structure only.
- Schemas contain API validation contracts.
- Real environment files stay outside `src/` and are never committed.
- User, Owner/Admin, and Super Admin authorization is enforced by FastAPI, not only by the frontend.
