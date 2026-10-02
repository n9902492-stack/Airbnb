# Nestora Frontend Architecture

The frontend is isolated inside `frontend/` and uses React + TypeScript + Vite.

## Folder layout

```text
frontend/
├── .env                 # Local frontend-only values. Never commit.
├── .env.example         # Safe template.
├── package.json
├── vite.config.ts
├── src/
│   ├── main.tsx         # React bootstrap
│   ├── App.tsx          # Application routes
│   ├── api/
│   │   ├── client.ts    # Shared HTTP client, token refresh, uploads
│   │   └── properties.ts
│   ├── components/      # Reusable UI
│   ├── pages/           # Route-level screens
│   ├── lib/             # Cross-feature helpers and API compatibility exports
│   ├── types.ts         # Shared UI types
│   └── styles.css       # Current shared visual system
└── Dockerfile
```

## Frontend dependency rule

```text
Page
  ↓
Reusable component
  ↓
API/domain helper
  ↓
src/api/client.ts
  ↓
FastAPI backend
```

React must never connect to PostgreSQL directly.

## Role areas

### Traveller/User
- Home and search
- Property details
- Wishlist and trip planning
- Checkout and payments
- My Trips
- Booking messages
- Reviews
- Trust/support tools

### Owner/Admin
- Property creation/editing
- Photos and detailed listing data
- Availability
- Pricing rules
- Reservations
- Earnings/payouts
- Services/experiences
- Co-host collaboration

### Super Admin
- Platform overview
- Listing moderation
- Identity moderation
- Booking controls
- Finance/payout controls
- Promotions
- Audit/trust operations

## Coding rules

1. Route-sized screens go in `src/pages`.
2. Shared UI belongs in `src/components`.
3. HTTP transport belongs only in `src/api/client.ts`.
4. Feature API modules should live in `src/api` as the app is gradually split from the compatibility barrel.
5. Never hard-code secrets or backend private keys in React.
6. Keep permission checks on the backend even if a frontend route is protected.
7. Prefer typed request and response contracts.
8. Do not mix owner, user, and super-admin page logic in one large screen when separate components are clearer.
