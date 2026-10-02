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


## Booking lifecycle and payments

Nestora now supports:

- PostgreSQL-backed availability and date blocking
- 15-minute unpaid reservation holds
- Automatic expiry of unpaid bookings
- Customer My Trips
- Owner reservation management
- Guest cancellation and refund calculation
- Razorpay-ready live checkout
- Signed Razorpay checkout verification
- HMAC-verified Razorpay webhooks
- Development/demo payment fallback

### Payment environment variables

Keep real keys only in `backend/.env`:

```env
BOOKING_HOLD_MINUTES=15

# Use demo locally, razorpay for live/test Razorpay checkout.
PAYMENT_PROVIDER=demo

RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
RAZORPAY_WEBHOOK_SECRET=

CANCELLATION_FULL_REFUND_HOURS=48
CANCELLATION_PARTIAL_REFUND_HOURS=24
CANCELLATION_PARTIAL_REFUND_PERCENT=50
```

To enable Razorpay:

```env
PAYMENT_PROVIDER=razorpay
RAZORPAY_KEY_ID=your_key_id
RAZORPAY_KEY_SECRET=your_key_secret
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret
```

Never put `RAZORPAY_KEY_SECRET` or `RAZORPAY_WEBHOOK_SECRET` in the frontend.

### Razorpay webhook

Configure the Razorpay webhook to call:

```text
POST https://YOUR_PUBLIC_API_DOMAIN/api/v1/payments/webhooks/razorpay
```

Subscribe at minimum to:

```text
payment.captured
```

The API validates the `X-Razorpay-Signature` before processing a webhook.

### Cancellation policy defaults

The current configurable development policy is:

```text
48+ hours before check-in: 100% refund
24–48 hours before check-in: 50% refund
Less than 24 hours: no refund
```

These values are configuration, not hard-coded business policy.

### Booking holds

A new unpaid booking receives an expiration time. By default it is held for 15 minutes. A backend lifecycle worker checks every minute and cancels expired unpaid bookings, which releases those dates back into availability.

### Apply latest migrations

```powershell
cd backend
.venv\Scripts\activate
alembic upgrade head
```

The current migration chain includes:

```text
20261002_01 initial auth/properties/bookings
20261002_02 reviews
20261002_03 transfers and property coordinates
20261002_04 availability and payments
20261002_05 booking expiry, cancellation and refunds
```


## Marketplace pipeline

The project now follows one connected marketplace pipeline rather than separate demo flows:

```text
LIVE POSTGRESQL PROPERTIES
        ↓
SEARCH + CATEGORY + GUEST FILTERS
        ↓
PROPERTY DETAIL
        ↓
ROOM PHOTOS + VERIFIED-STAY REVIEWS
        ↓
WISHLIST (optional)
        ↓
LIVE AVAILABILITY
        ↓
OPTIONAL MAP-BASED TRANSFER
        ↓
RESERVATION + 15-MINUTE HOLD
        ↓
CHECKOUT
        ↓
RAZORPAY / DEMO PAYMENT PROVIDER
        ↓
CONFIRMED BOOKING
        ↓
MY TRIPS + OWNER RESERVATIONS
        ↓
GUEST ↔ OWNER BOOKING CHAT
        ↓
IN-APP NOTIFICATIONS + EMAIL RECEIPTS
        ↓
CANCELLATION / REFUND
        ↓
OWNER EARNINGS
        ↓
COMPLETED STAY
        ↓
VERIFIED CUSTOMER REVIEW
```

### New marketplace modules

Backend modules added without changing the existing service boundaries:

```text
models/
  wishlist.py
  message.py
  notification.py

api/routes/
  wishlist.py
  messages.py
  notifications.py

services/
  notification_service.py
```

The public property endpoint supports PostgreSQL filtering:

```text
GET /api/v1/properties?q=
GET /api/v1/properties?city=
GET /api/v1/properties?category=
GET /api/v1/properties?guests=
GET /api/v1/properties?min_price=
GET /api/v1/properties?max_price=
```

Owner financial reporting:

```text
GET /api/v1/owner/earnings
```

Booking chat:

```text
GET  /api/v1/messages/{booking_id}
POST /api/v1/messages/{booking_id}
```

Wishlist:

```text
GET    /api/v1/wishlist
POST   /api/v1/wishlist/{property_id}
DELETE /api/v1/wishlist/{property_id}
```

Notifications:

```text
GET  /api/v1/notifications
POST /api/v1/notifications/{notification_id}/read
```

Super Admin booking controls:

```text
GET  /api/v1/super-admin/bookings
POST /api/v1/super-admin/bookings/{booking_id}/cancel
```

Admin cancellation reuses the normal cancellation/refund service; it does not bypass payment/refund logic.

### Latest migration

```text
20261002_06_wishlist_messages_notifications.py
```

Run the full migration chain with:

```powershell
cd backend
.venv\Scripts\activate
alembic upgrade head
```


## Production hardening and full stay lifecycle

The marketplace pipeline now includes production-oriented pricing, booking completion, owner payouts and authentication abuse controls.

### Pricing order

Booking totals are calculated on the backend in this order for every booked night:

```text
Seasonal/date pricing rule
        ↓ if none
Weekend price (Friday/Saturday)
        ↓ if none
Base nightly price
```

Owners can also configure:

```text
minimum stay nights
maximum stay nights
seasonal minimum stay
weekend nightly price
```

Owner pricing endpoints:

```text
GET    /api/v1/owner/properties/{property_id}/pricing-rules
POST   /api/v1/owner/properties/{property_id}/pricing-rules
DELETE /api/v1/owner/properties/{property_id}/pricing-rules/{rule_id}
```

### Completed stay lifecycle

The booking lifecycle worker now performs both:

```text
unpaid pending booking → cancelled after hold expiry
confirmed booking → completed after checkout date
```

When a stay becomes completed:

```text
booking → completed
owner payout → ready
guest → review-available notification
owner → payout-ready notification
```

This connects completed stays directly to verified review eligibility.

### Platform commission and owner payouts

Default platform commission:

```env
PLATFORM_COMMISSION_PERCENT=12
```

Owner payout is based on accommodation revenue only:

```text
nightly accommodation + cleaning fee
        ↓
Nestora owner commission
        ↓
owner payable
```

The guest service fee and optional transfer are not included in the owner's accommodation payout.

Refunds proportionally recalculate:

```text
remaining accommodation revenue
platform commission
owner payable
```

Owner payout endpoint:

```text
GET /api/v1/owner/payouts
```

Super Admin finance endpoints:

```text
GET  /api/v1/super-admin/finance
POST /api/v1/super-admin/payouts/{payout_id}/mark-paid
```

Important: `mark-paid` records that an external payout has been completed. It does not itself send money to the owner's bank account. A payout provider integration must be added before automatic bank payouts are enabled.

### Authentication abuse protection

Database-backed controls now include:

```env
LOGIN_MAX_ATTEMPTS=5
LOGIN_ATTEMPT_WINDOW_MINUTES=15
OTP_RESEND_COOLDOWN_SECONDS=60
```

Failed login attempts are stored in `auth_events`; excessive failures return HTTP 429. Verification OTP resend also has a cooldown.

### Production HTTP security

Production startup rejects the default/weak JWT secret and incomplete Razorpay configuration.

Set API hostnames explicitly:

```env
ALLOWED_HOSTS=api.example.com,localhost
```

Security headers and TrustedHost middleware are enabled in production.

### Migration 07

Apply:

```powershell
cd backend
.venv\Scripts\activate
alembic upgrade head
```

Migration:

```text
20261002_07_pricing_payout_security.py
```

adds:

```text
properties.weekend_price_per_night
properties.minimum_stay_nights
properties.maximum_stay_nights

pricing_rules
owner_payouts
auth_events
```

The current migration chain is:

```text
01 auth / properties / bookings
02 verified reviews
03 transfer and map coordinates
04 availability and payments
05 expiry / cancellation / refunds
06 wishlist / messages / notifications
07 pricing / payouts / auth security
```
