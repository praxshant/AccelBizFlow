# Accel BizFlow backend

## Run locally

From `C:\Users\ACER\Downloads\AirtelSync`:

```powershell
python -m pip install -r backend\requirements-dev.txt
$env:PYTHONPATH = "backend"
python -m uvicorn app.main:app --app-dir backend --reload
```

The API is available at `http://127.0.0.1:8000`. The product-engine endpoint is:

```text
POST /api/recommendations/evaluate
```

Implemented backend phases:

- Phase 1: deterministic catalogue eligibility and dependency validation.
- Phase 2: versioned midpoint pricing, persisted quotes, quote modification, and idempotent acceptance (`/api/quotes`).
- Phase 3: context-preserving advisor discovery with validated profiles (`/api/advisor`); Ollama remains optional and cannot decide eligibility.
- Phase 4: simulated feasibility, explicit consent, private local document processing, synthetic GSTIN/Udyam lookup, KYC status and reviewer audit routes (`/api/kyc`).
- Phase 5: accepted-quote order creation, validated order transitions, payment simulation, installation scheduling, and tracker responses (`/api/orders`).
- Phase 6: historical funnel/segment analytics, point-in-time lead scoring, partner queues, and assignments (`/api/analytics` and `/api/partner`).

The catalogue does not define a separate setup-fee basis. The implemented rate card uses the catalogue's one-time setup amount per recommended product quantity and records the pricing version in every quote.

## Test

```powershell
$env:PYTHONPATH = "backend"
python -m pytest backend\tests -q
```

## Optional Ollama fallback

The advisor provider seam supports a local Ollama model for structured business-profile extraction:

```powershell
$env:OLLAMA_BASE_URL = "http://localhost:11434"
$env:OLLAMA_MODEL = "llama3.2"
```

Ollama is not used for catalogue eligibility, dependency validation, pricing, KYC approval, or order activation. Those decisions remain deterministic backend operations.

The KYC image set is synthetic. The local OCR boundary intentionally records unread/low-confidence specimens as `MANUAL_REVIEW` rather than fabricating extracted identity fields. No raw document contents or identity numbers are logged.

## Environment

Copy `backend\.env.example` to `.env` and set values as needed:

- `ADVISOR_PROVIDER=ollama` enables the optional local Ollama extraction call.
- `OLLAMA_BASE_URL` and `OLLAMA_MODEL` configure Ollama.
- `KYC_REVIEWER_ID` is the local development reviewer identity fallback. Production requires real authentication middleware; this prototype does not claim production identity verification.

The SQLite database is created at `backend\bizflow.sqlite3`. To process all supplied KYC specimens and write a machine-readable result, run:

```powershell
$env:PYTHONPATH = "backend"
python backend\scripts\process_kyc_dataset.py
```

Generated summary: `backend\data\kyc_processing_summary.json`.

## API groups

- `POST /api/recommendations/evaluate`
- `POST/GET/PATCH /api/quotes`
- `POST/GET /api/advisor`
- `POST/GET /api/kyc`
- `POST/GET /api/orders`
- `GET /api/analytics/funnel`
- `GET /api/analytics/segments`
- `GET /api/analytics/leads/{lead_id}/score`
- `GET/POST /api/partner`

Feasibility, payment, coverage, scheduling, OCR registries, and payment are explicitly simulated or local-only; they are not production integrations.

## Frontend

The React/Vite frontend is in `..\frontend`. Start the API first, then run:

```powershell
cd frontend
npm install
npm run dev
```

The frontend integration audit and implementation report are in
`..\docs\FRONTEND_INTEGRATION_AUDIT.md` and
`..\docs\FRONTEND_IMPLEMENTATION_REPORT.md`.
