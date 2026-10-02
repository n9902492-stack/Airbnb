# Nestora production runbook

## Runtime layout

Production is separated into four responsibilities:

```text
web (Nginx + React)
        ↓
api (FastAPI)
        ↓
PostgreSQL

worker (Redis jobs + booking lifecycle + payouts)
        ↓
Redis

property images
        ↓
S3-compatible object storage
        ↓
CDN
```

Use:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

The production Compose file runs Alembic migrations before starting the API and worker.

## Sessions

- Access token: short-lived JWT, default 15 minutes.
- Refresh token: random opaque token in an HttpOnly cookie.
- Only the SHA-256 hash of the refresh token is stored in PostgreSQL.
- Refresh tokens rotate on every refresh.
- Logout revokes the current refresh session.
- Password reset revokes every existing refresh session for the user.
- In production set `REFRESH_COOKIE_SECURE=true`.

## Redis jobs

The dedicated worker handles:

- unpaid booking expiry;
- automatic stay completion;
- automatic Razorpay Route payouts;
- booking confirmation email;
- cancellation email.

The API can run an in-process worker locally. In production the Compose API sets `JOB_WORKER_ENABLED=false` and starts the dedicated worker service.

## Object storage and CDN

Set:

```env
STORAGE_PROVIDER=s3
S3_BUCKET=...
S3_REGION=...
S3_ACCESS_KEY=...
S3_SECRET_KEY=...
CDN_BASE_URL=https://cdn.example.com
```

`S3_ENDPOINT_URL` is optional for AWS S3 and can be set for S3-compatible storage such as Cloudflare R2, MinIO or another compatible provider.

Uploads are validated as real JPEG, PNG or WebP content before storage. Files are stored under immutable random object keys and returned through the configured CDN base URL.

## Monitoring

Health endpoints:

```text
GET /health/live
GET /health/ready
```

Metrics:

```text
GET /metrics
```

The API exposes Prometheus request counters and latency histograms.

Set `SENTRY_DSN` to enable FastAPI exception reporting. Every HTTP response also receives:

```text
X-Request-ID
X-Response-Time-Ms
```

Use the request ID to correlate application errors with audit records and logs.

## Audit trail

Privileged operations are stored in PostgreSQL `audit_logs`.

Super Admin can review:

```text
GET /api/v1/super-admin/audit-logs
```

Current audited operations include payout account assignment, manual payout completion, property moderation and administrator booking cancellation.

## GST and invoices

GST support is intentionally disabled by default:

```env
GST_ENABLED=false
GST_RATE_PERCENT=18
```

Do not enable GST solely because the example rate is present. Configure the tax treatment only after confirming how your marketplace, accommodation supply, service fee and transport charges should be invoiced for your registered entity.

When enabled, the backend:

1. calculates GST during checkout;
2. includes it in the Razorpay order amount;
3. issues a matching invoice after successful payment.

Traveller invoice endpoint:

```text
GET /api/v1/invoices/{booking_id}
```

## Razorpay Route payouts

Automatic owner-bank payout still requires:

- Route activated for your Razorpay merchant account;
- each owner onboarded and KYC-approved as a Route Linked Account;
- the verified `acc_...` ID attached by Super Admin.

Nestora does not store raw owner bank credentials.

## CI

GitHub Actions runs on pull requests and pushes:

```text
Backend:
- install dependencies
- compile Python
- pytest

Frontend:
- TypeScript check
- Vite production build

Containers:
- backend Docker build
- frontend Docker build
```

Do not merge production changes if CI is red.

## Deployment checklist

Before going live:

- use managed PostgreSQL or encrypted persistent PostgreSQL storage;
- use managed Redis or durable Redis with authentication/network isolation;
- set a strong production `SECRET_KEY`;
- enable HTTPS;
- set `REFRESH_COOKIE_SECURE=true`;
- set the exact production `FRONTEND_URL` and `ALLOWED_HOSTS`;
- configure S3-compatible object storage and CDN;
- configure SMTP;
- configure Sentry;
- configure Razorpay live credentials and webhook secret;
- configure Route only after linked-account onboarding works;
- review GST/invoice requirements with your accountant/tax adviser;
- run `alembic upgrade head`;
- verify `/health/ready` and `/metrics`;
- test one complete booking, cancellation/refund and owner payout in provider test mode before enabling live transactions.
