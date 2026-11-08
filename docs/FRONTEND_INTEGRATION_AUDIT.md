# Frontend integration audit

## Baseline

The repository contains a FastAPI modular monolith under `backend/` and no
previous frontend. The backend exposes catalogue, leads, advisor sessions,
recommendations, feasibility, quotes, KYC, orders, analytics and partner
operations routes. It uses SQLite persistence and synthetic case data.

The frontend uses the real API contracts. It does not duplicate eligibility,
pricing, feasibility, KYC, payment or order decisions.

## API adapters

`frontend/src/api.ts` is the centralized Axios client and injects a stored
Bearer token when one exists. The app currently consumes:

- `/leads`
- `/advisor/sessions`
- `/catalog/products`
- `/recommendations/evaluate`
- `/feasibility/check` through the backend compatibility route
- `/quotes`
- `/kyc/cases`
- `/orders`
- `/analytics/funnel`
- `/partner/queue`

The existing backend still supports a specimen-reference KYC route rather than
a multipart customer upload route. The UI labels specimen processing honestly
and does not pretend a selected local filename is a binary upload.

## Security limitations

The repository's `/api/auth/token` endpoint is explicitly prototype-only and
issues a JWT from a caller-supplied identity and role. The frontend does not
manufacture tokens or treat the role selector as authorization. Production
identity verification and customer resource ownership enforcement remain
backend work.

## Design and state handling

The frontend is a responsive React/Vite TypeScript application with a shared
design system in `src/styles.css`. It includes customer discovery, advisor,
catalogue, recommendations, quotes, KYC, order tracking, and operations
views. API failures appear as actionable toast messages; loading, empty,
success, retry and manual-review states are represented in the relevant views.
