# Frontend implementation report

## Status

**READY WITH DOCUMENTED LIMITATIONS**

The customer and operations frontend is implemented against the current
FastAPI backend. It is not presented as production-ready authentication or
document-upload infrastructure.

## Implemented

- Business lead creation and persisted lead context.
- Session-backed advisor chat with structured profile display.
- Live catalogue search and category filtering.
- Backend recommendation evaluation and bundle selection.
- Backend-calculated quote display and acceptance.
- Consent-gated synthetic KYC specimen processing.
- Persisted order tracker and simulated payment actions.
- Historical funnel and live partner queue views.
- Responsive enterprise SaaS visual system.

## Backend compatibility work

Added catalogue/lead compatibility entities and API wiring where required by
the frontend. Existing backend business services were reused. No frontend
eligibility or pricing engine was added.

## Known limitations

1. The backend authentication token endpoint is prototype-only; it accepts a
   caller-provided role and must be replaced with OIDC or another real identity
   provider before production use.
2. KYC currently processes synthetic specimen references. A genuine multipart
   upload endpoint and authenticated applicant ownership boundary are not yet
   available, so the frontend does not fake binary upload behavior.
3. Feasibility, payment, scheduling and registry integrations are simulated by
   design.
4. The current backend route set does not expose a complete customer lead
   ownership model or live order creation UI from the quote acceptance screen;
   the order tracker supports retrieving persisted orders by ID.

## Run

From the repository root:

```powershell
python -m pip install -r backend\requirements-dev.txt
$env:PYTHONPATH = "backend"
python -m uvicorn app.main:app --app-dir backend --reload

cd frontend
npm install
npm run dev
```

Set `frontend\.env` from `.env.example` when the API is not at the default
`http://127.0.0.1:8000/api`.

## Verification

The backend regression suite remains the source of truth for backend decisions.
Run it with:

```powershell
$env:PYTHONPATH = "backend"
python -m pytest backend\tests -q
```

Build the frontend with:

```powershell
cd frontend
npm run build
```
