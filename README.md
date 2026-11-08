# Accel BizFlow

Accel BizFlow is a full-stack prototype for helping small businesses discover
eligible products, receive quotes, complete simulated KYC, place orders, and
track fulfilment. The project includes a deterministic FastAPI backend, a
React/Vite frontend, synthetic registry data, analysis notebooks, and supporting
documentation.

> This is a prototype. Feasibility, payment, coverage, scheduling, OCR
> registries, and advisor integrations are simulated or local-only.

## Repository layout

```text
backend/                         FastAPI API, services, migrations, and tests
frontend/                        React/Vite web application
YTL_TrackA_Udyam_Digital_Data/   Synthetic catalogue and registry data
analysis/                         Jupyter analysis notebooks
docs/                             Audits, implementation notes, and reports
6ad9d4887d445_airtel_sync/        Case materials
docker-compose.yml                Backend container configuration
Roadmap.md                        Product roadmap
```

## Prerequisites

- Python 3.11 or newer
- Node.js 18 or newer and npm
- Docker Desktop (optional)

## Run locally

### Backend

From the repository root:

```powershell
python -m venv backend\.venv
backend\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements-dev.txt
Copy-Item backend\.env.example backend\.env
$env:PYTHONPATH = "backend"
python -m uvicorn app.main:app --app-dir backend --reload
```

The API is available at `http://127.0.0.1:8000`. Interactive API
documentation is available at `http://127.0.0.1:8000/docs`.

### Frontend

In a second terminal:

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

The frontend is available at the URL printed by Vite, normally
`http://localhost:5173`.

### Docker

```powershell
docker compose up --build
```

## Test and build

Run backend tests:

```powershell
$env:PYTHONPATH = "backend"
python -m pytest backend\tests -q
```

Build the frontend:

```powershell
cd frontend
npm run build
```

## Main API groups

- `POST /api/recommendations/evaluate` - product eligibility and recommendations
- `/api/quotes` - quote creation, modification, and acceptance
- `/api/advisor` - business-profile and advisor discovery flows
- `/api/kyc` - local document processing and review status
- `/api/orders` - order, payment, installation, and tracking flows
- `/api/analytics` - funnel, segments, and lead scoring
- `/api/partner` - partner queues and assignments

## Configuration

Copy the example environment files before running locally:

- Backend: `backend\.env.example`
- Frontend: `frontend\.env.example`

Never commit `.env` files, credentials, or production secrets. The local
SQLite database is generated at `backend\bizflow.sqlite3` and is intentionally
ignored by Git.

## Synthetic data and KYC

The files in `YTL_TrackA_Udyam_Digital_Data` are synthetic inputs for local
development and demos. KYC processing records unreadable or low-confidence
specimens as `MANUAL_REVIEW` rather than fabricating identity fields. To
generate the local processing summary:

```powershell
$env:PYTHONPATH = "backend"
python backend\scripts\process_kyc_dataset.py
```

## Optional Ollama advisor

The advisor extraction seam can use a local Ollama model:

```powershell
$env:ADVISOR_PROVIDER = "ollama"
$env:OLLAMA_BASE_URL = "http://localhost:11434"
$env:OLLAMA_MODEL = "llama3.2"
```

Eligibility, pricing, KYC approval, and order activation remain deterministic
backend operations.
