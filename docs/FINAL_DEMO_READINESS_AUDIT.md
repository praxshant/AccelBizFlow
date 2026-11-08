# Accel BizFlow v2.0 — Final Demo Readiness Audit

Audit date: 2026-11-08  
Audit mode: independent, read-only application audit. No application source or roadmap file was changed.

## A. Executive verdict

**NOT READY FOR LIVE DEMONSTRATION.**

The backend is runnable and its targeted regression suite passes, but the actual React application cannot submit its first lead from the browser because the FastAPI application has no CORS middleware. The browser records a failed preflight (`OPTIONS /api/leads` returns `405` without `Access-Control-Allow-Origin`), so the customer journey stops at the first interaction.

The frontend also does not implement the required end-to-end path after quote acceptance: there is no feasibility screen, no order-creation action, no installation scheduling action, and no real operations assignment control. These are not cosmetic limitations.

| Area | Assessment |
|---|---|
| Backend readiness | **Conditionally ready for isolated API demonstration**; 78 targeted tests pass and `/health` reports 25 products. |
| Frontend readiness | **Not ready**; browser-to-API CORS failure blocks lead creation. |
| End-to-end integration | **Not ready**; the UI omits required journey stages and cannot reach the backend in the browser as configured. |
| Visual/product experience | **Moderate polish, not demonstration-ready**; desktop presentation is credible, but mobile overflow and dead controls remain. |
| Security readiness | **Not production-ready**; caller-selected JWT roles and missing resource ownership are explicitly confirmed in source. |
| Production readiness | **Not ready**. |

Final answer to the audit question: **No. The current application cannot be opened and operated live from the first customer interaction through order tracking and partner operations with genuine backend behavior.**

## B. Repository verification

The workspace is **not a Git repository**: `git status --short --branch` returned `fatal: not a git repository`. Branch and uncommitted-work verification therefore could not be completed.

Inspected:

- `Roadmap.md`
- `ACCEL_BIZFLOW_BACKEND_AUDIT_REPORT.md`
- `BACKEND_REMEDIATION_REPORT.md`
- `docs/FRONTEND_INTEGRATION_AUDIT.md`
- `docs/FRONTEND_IMPLEMENTATION_REPORT.md`
- `backend/app/`, `backend/tests/`, `backend/migrations/`
- `backend/bizflow.sqlite3`
- `backend/alembic.ini`, `backend/.env.example`, `backend/README.md`
- `frontend/src/`, `frontend/package.json`, `frontend/package-lock.json`, `frontend/vite.config.ts`, `frontend/.env.example`
- `analytics/`, `YTL_TrackA_Udyam_Digital_Data/`, and `docker-compose.yml`

The active database is SQLite at `backend\bizflow.sqlite3`. The application loads the catalogue and synthetic registries from `YTL_TrackA_Udyam_Digital_Data`.

## C. Environment and test results

### Environment

The mandated `torch26` environment exists and reports:

- Python 3.10.19
- FastAPI 0.136.1
- SQLAlchemy 2.0.23
- Pydantic 2.13.3
- PyTorch installed
- EasyOCR installed

The bundled `backend\.venv` is not provisioned with the required packages (`fastapi` and `pytest` are missing). Node.js is v24.21.0 and npm is 11.5.2.

### Commands and actual results

| Command | Result |
|---|---|
| `Set-Location backend; conda run -n torch26 python -m pytest tests -q` | **78 passed in 162.86s** |
| `Set-Location backend; conda run -n torch26 python -m pytest -q` | **Failed during collection** because `backend\scripts\patch_test.py` attempts to open `backend\tests\test_phase234.py` using an invalid relative path. |
| `Set-Location frontend; npm run build` | **Passed**: TypeScript build and Vite production build; 98 modules transformed. |
| `conda run -n torch26 python -m alembic upgrade head --sql` | **Passed**: migration SQL generated without applying it. |
| `GET http://127.0.0.1:8000/health` | **200**, `{"status":"ok","catalogue_products":25}` |
| `GET http://127.0.0.1:8000/openapi.json` | **200**, 38 registered paths including `/health`. |
| `GET http://127.0.0.1:8000/api/analytics/funnel` | **200**; historical baseline is 5,000 leads, 368 activations, 7.36%; live counts are returned separately. |
| `OPTIONS /api/leads` with browser Origin and requested POST headers | **405**, no CORS headers. |
| `npm run lint` | **Not available**; `frontend/package.json` defines no lint script. |

The development servers started successfully at `http://127.0.0.1:5173` and `http://127.0.0.1:8000`.

## D. Frontend quality assessment

### Visual scores

| Criterion | Score | Evidence |
|---|---:|---|
| Overall visual quality | 7/10 | Consistent enterprise-style cards, typography, spacing and clear primary actions on the home screen. |
| Consistency | 7/10 | Shared button, card, status and field styles; some screens expose unfinished operations behavior. |
| Usability | 4/10 | The intended flow is understandable, but the first submit fails in-browser and later required stages are absent. |
| Responsiveness | 5/10 | The 390px browser check reported `scrollWidth=390` and `clientWidth=375`, indicating horizontal overflow. |
| Professional presentation | 6/10 | Desktop home screen is polished enough for a mock review; live failure and dead controls make it unsafe for a real demo. |
| Demonstration readiness | 2/10 | The browser cannot complete lead creation, and the full journey is not represented in the UI. |

The desktop home screen rendered cleanly. The mobile check exposed horizontal overflow, and the fixed top navigation remains dense at narrow widths. No browser console error was suppressed; the lead submission produced a visible `Network Error` toast and CORS console error.

## E. API integration matrix

| Frontend feature | Backend route(s) | Result |
|---|---|---|
| Lead creation | `POST /api/leads` | Implemented in code, but browser execution blocked by CORS. Returned leads are not persisted; `GET /api/leads/{lead_id}` only scores rows from historical CSV data. |
| Advisor | `POST /api/advisor/sessions`, `POST /api/advisor/sessions/{id}/messages` | Implemented in code; not reached through the browser because lead creation stops first. |
| Catalogue/search | `GET /api/catalog/products` | Backend live response returned 25 products; frontend filtering is client-side over that response. |
| Recommendations | `POST /api/recommendations/evaluate` | Backend live response worked; frontend calls the route but uses untyped `any` recommendation data. |
| Feasibility | `POST /api/feasibility/check` | Backend supports all four simulated states; no frontend view or call exists. |
| Quote | `POST /api/quotes`, `PATCH /api/quotes/{id}/items`, `POST /api/quotes/{id}/accept` | Backend quote creation/acceptance worked; frontend accepts the quote but immediately routes to KYC without creating an order. |
| KYC | `POST/GET /api/kyc/cases...` | Specimen-reference flow exists; no multipart upload. The path document route still requires `applicant_id` in the request body because `DocumentRequest` requires it. |
| Orders | `POST/GET /api/orders`, transition/payment/installation routes | Backend prerequisites and state machine are present; frontend has retrieval/payment UI only and no order creation or lifecycle controls. |
| Operations | `GET /api/partner/queue`, `POST /api/partner/assignments` | Queue retrieval is displayed; the frontend “Open case” control only flashes text and does not call the assignment API. |
| Analytics | `GET /api/analytics/funnel` | Backend separates historical and live values, but the frontend reads `funnel.leads`, `funnel.activated`, and `funnel.conversion_rate` while the response nests them under `historical_baseline`; the displayed historical cards therefore fall back to `—`/`0.00%`. |

## F. Customer journey results

| Stage | Result | Evidence |
|---|---|---|
| 1. Lead creation | **Failed in browser; partially passed API-only** | Direct `POST /api/leads` returned `201`; browser POST failed at CORS preflight. The response is not persisted as a lead record. |
| 2. Advisor | **Not tested through frontend** | Backend routes and persistence exist, but the browser cannot pass Stage 1. No browser claim is made. |
| 3. Catalogue/recommendations | **Passed API-only; not end-to-end** | `GET /api/catalog/products` returned 25 products. A live profile evaluation returned 17 eligible products and did not incorrectly include P10 for a one-site profile. |
| 4. Feasibility | **Partially passed API-only; failed frontend coverage** | Live API returned `AVAILABLE` for Jaipur, `ALTERNATIVE_AVAILABLE` for an “alternative” location, `SURVEY_REQUIRED` for a survey location, and `NOT_FEASIBLE` for “Remote Village”. No UI exposes this stage. |
| 5. Quote builder | **Partially passed** | Backend generated midpoint pricing (`P01`, ₹1,099 monthly) and enforced “accepted quote” before order creation. Frontend has create/edit/accept controls but no idempotency key and does not create the subsequent order. |
| 6. KYC | **Partially passed** | Consent and specimen routes exist; the UI truthfully labels synthetic processing. A path document request without the duplicated body `applicant_id` returned `422`, showing a contract mismatch. Multipart uploads and authenticated applicant ownership are unavailable. |
| 7. Order lifecycle | **Backend partially passed; frontend failed** | Direct order creation rejected an unaccepted quote with `409`; accepted quote created an order; transition to `KYC_VERIFIED` was rejected with `409` while the KYC case was `ACTION_REQUIRED`. The frontend never creates the order or exposes transition/scheduling controls. |
| 8. Operations | **Partially passed API-only; frontend failed** | Queue returned live records and assignment API returned `201`; the frontend queue action does not persist assignment changes and has no filters or reviewer/partner workflow. |
| 9. Analytics | **Partially passed** | Backend returned historical and live sections separately. Frontend field mapping is incorrect, so historical cards are blank/zero rather than displaying 5,000/368/7.36%. |

## G. Operations workspace results

- Sales/lead visibility: historical scoring exists, but newly created leads are not persisted and the frontend does not show a sales lead list.
- KYC reviewer: the backend requires `kyc_reviewer`/`kyc_admin`; a token with role `sales` received `403` for review, which is correct. The frontend role selector does not authenticate or invoke reviewer actions.
- Partner queue: queue retrieval works and reports live records, but assignment changes are not wired from the UI.
- Installation exceptions: backend queue logic includes blocked installation orders, but the frontend has no exception handling or installation controls.
- Analytics: historical and live sources are returned separately by the backend but displayed incorrectly by the frontend.

## H. Security findings

### Local isolated demo safety

Acceptable only with synthetic records, localhost binding, restricted network exposure, and an operator who understands that `/api/auth/token` is a prototype token minting endpoint. Simulated feasibility, payment, scheduling and registry behavior is clearly identified in the UI/backend documentation.

### Multi-user demo safety

Not safe. `POST /api/auth/token` accepts caller-supplied `identity` and `role`, so any caller can mint an admin token. Lead, KYC, order and document routes do not establish applicant/resource ownership. Order reads and mutations are also not protected by an authenticated-user dependency.

### Production readiness

Not production-ready. The prototype authentication limitation is explicitly documented, but it remains a critical security boundary and must not be presented as real authorization. CORS is also absent, and the frontend currently relies on a role selector rather than an authenticated session.

## I. Roadmap compliance

### Compliant or substantially compliant

- Modular FastAPI monolith structure remains intact.
- Catalogue has 25 products and is loaded through the backend.
- Eligibility and pricing decisions are backend-controlled.
- Four feasibility states are implemented as simulated responses.
- Four KYC statuses are represented.
- Quote items, KYC documents, order events, payments and installations have persistence models.
- Historical analytics and live prototype counts are returned as separate objects.
- Synthetic integrations are labelled as simulated/local.

### Partially compliant or non-compliant

- The complete customer journey is not connected in the frontend.
- Lead creation is not persisted as a live lead record.
- Binary multipart document upload is not implemented.
- Resource ownership and production identity verification are not implemented.
- Operations assignment and exception handling are not implemented in the frontend.
- The frontend does not expose feasibility, order creation, order transitions or installation scheduling.
- Frontend analytics does not consume the actual nested response shape.

## J. P0–P3 defect register

### P0-01 — Browser cannot submit a lead because CORS is absent

- **Area:** Frontend/backend integration.
- **Location:** `backend/app/main.py` FastAPI application setup; `frontend/src/App.tsx`, `Home.submit`.
- **Evidence:** Browser POST to `http://127.0.0.1:8000/api/leads` produced a CORS console error. Direct preflight returned `405` with no `Access-Control-Allow-Origin`.
- **Reproduction:** Start both development servers, open the frontend, complete the lead form, click “Create lead & start discovery”.
- **Demo impact:** Blocks the first customer action.
- **Minimum correction:** Add narrowly scoped development CORS configuration for the actual frontend origin and verify preflight plus credential/header behavior.
- **Blocks sign-off:** Yes.

### P0-02 — Required end-to-end stages are absent from the frontend

- **Area:** Customer journey.
- **Location:** `frontend/src/App.tsx`, `QuoteBuilder`, `Kyc`, `Orders`.
- **Evidence:** Quote acceptance routes directly to `kyc`; KYC only processes a specimen and never calls `POST /api/orders`; there is no feasibility view, order creation control, transition control, or installation scheduling control.
- **Reproduction:** Inspect the rendered flow after quote acceptance or follow the `onAccepted` callback in `QuoteBuilder`.
- **Demo impact:** The advertised journey cannot reach order tracking or activation.
- **Minimum correction:** Wire feasibility, order creation, and the required persisted order lifecycle actions into the actual UI, with visible backend responses and errors.
- **Blocks sign-off:** Yes.

### P0-03 — Prototype token issuance and missing ownership make multi-user use unsafe

- **Area:** Authentication and authorization.
- **Location:** `backend/app/api/auth.py`, `issue_token`; `backend/app/api/orders.py`; `backend/app/api/kyc.py`; `backend/app/api/leads.py`.
- **Evidence:** The token endpoint accepts caller-provided identity/role. A caller can request `admin`; resource routes do not enforce ownership. A sales token correctly received `403` for reviewer action, but the broader resource boundary is absent.
- **Reproduction:** `POST /api/auth/token` with any synthetic identity and `role=admin`; access resource IDs from another identity.
- **Demo impact:** Unsafe beyond a tightly isolated synthetic local demo.
- **Minimum correction:** Replace token minting with trusted identity verification and enforce owner/tenant checks on every resource read and mutation.
- **Blocks sign-off:** Yes for any multi-user or production-like demo; local-only demo remains conditional.

### P1-01 — Newly created leads are not persisted or retrievable

- **Area:** Lead lifecycle.
- **Location:** `backend/app/api/leads.py`, `create_lead` and `get_lead`.
- **Evidence:** `POST /api/leads` returns a generated lead object, but `get_lead` scores only the historical CSV through `AnalyticsService`; no lead table/write occurs.
- **Reproduction:** Create a new lead, then request `GET /api/leads/{returned_id}`.
- **Demo impact:** The same live lead cannot be reliably propagated through the journey.
- **Minimum correction:** Persist the lead and retrieve/score the persisted record with an explicit historical/live distinction.
- **Blocks sign-off:** Yes for the complete customer journey.

### P1-02 — KYC path contract duplicates applicant ID in the body

- **Area:** API contract/KYC.
- **Location:** `backend/app/api/kyc.py`, `case_document`; `backend/app/schemas/kyc.py`, `DocumentRequest`.
- **Evidence:** `POST /api/kyc/cases/{id}/documents` without `applicant_id` in the body returned `422`, although the path already identifies the applicant. The current frontend works around this by sending the field twice.
- **Demo impact:** External clients using the documented path shape can fail; binary upload remains unavailable.
- **Minimum correction:** Make the path parameter authoritative, remove the duplicated body requirement, and add an explicit multipart route when real uploads are supported.
- **Blocks sign-off:** No for the isolated specimen flow; yes for a truthful upload demonstration.

### P1-03 — Operations controls are visually present but non-functional

- **Area:** Partner operations.
- **Location:** `frontend/src/App.tsx`, `Operations`.
- **Evidence:** “Open case” only calls `flash("Assignment changes are saved through the partner API.")`; it does not call `POST /api/partner/assignments` or open a case.
- **Demo impact:** Partner assignment/exception handling cannot be demonstrated.
- **Minimum correction:** Add real assignment, owner/status/filter controls, persist changes, reload them, and surface API errors.
- **Blocks sign-off:** Yes for operations demonstration.

### P1-04 — Analytics response is consumed with the wrong shape

- **Area:** Operations analytics.
- **Location:** `frontend/src/App.tsx`, `Operations`; `backend/app/services/analytics.py`, `funnel`.
- **Evidence:** Backend returns `historical_baseline.leads`, `historical_baseline.activated`, and `historical_baseline.conversion_rate`; frontend reads `funnel.leads`, `funnel.activated`, and `funnel.conversion_rate`. The fallback displays `—` and `0.00%`.
- **Demo impact:** Historical baseline appears missing or zero and undermines trust in the dashboard.
- **Minimum correction:** Use typed response contracts and render the nested historical and live fields separately.
- **Blocks sign-off:** Yes for analytics claims.

### P2-01 — Mobile layout overflows horizontally

- **Area:** Responsive UX.
- **Location:** `frontend/src/styles.css`, topbar/hero/form layout rules.
- **Evidence:** At a 390px browser viewport, `scrollWidth` was 390px while the usable `clientWidth` was 375px.
- **Reproduction:** Open the home screen at 390px width and inspect document dimensions/scrolling.
- **Demo impact:** Minor for desktop, but visibly weak on mobile/tablet demonstrations.
- **Minimum correction:** Add narrow-width layout rules for navigation, form grids and fixed-width content.
- **Blocks sign-off:** No for desktop-only; yes if mobile is part of the demo.

### P2-02 — Human assistance and case actions are misleading

- **Area:** UX/action integrity.
- **Location:** `frontend/src/App.tsx`, `Home` and `Operations`.
- **Evidence:** “Talk to a specialist” calls `window.alert`; “Open case” only displays a toast. Neither records or opens a backend workflow.
- **Demo impact:** A live operator may believe a request/action was persisted when it was not.
- **Minimum correction:** Implement the backend action or label these controls as informational/non-functional.
- **Blocks sign-off:** No for a controlled demo if clearly disclosed; otherwise yes.

## K. Demo execution script

No truthful 3-minute full customer demo can be written for the current build because P0-01 stops the browser at lead creation and P0-02 omits required stages.

A limited, honest API/UI review script is possible:

1. Open the home screen and disclose that backend CORS currently prevents browser submission.
2. Show the live catalogue response containing 25 products.
3. Use the backend recommendation endpoint with a synthetic professional-office profile and show the deterministic eligible/ineligible response.
4. Call feasibility with one normal, one alternative, one survey and one remote location; label all four outputs simulated.
5. Create and accept a quote through the API, showing backend midpoint pricing and the pre-acceptance order rejection.
6. Create a KYC specimen case with explicit consent and show an action-required/manual-review outcome; do not call it a real upload.
7. Attempt `KYC_VERIFIED` on the order and show the backend `409` prerequisite rejection.
8. Show the operations queue as read-only and disclose that assignment controls are not wired.

This is an audit/demo limitation script, not a sign-off demo of the advertised product.

## L. Final acceptance checklist

- [ ] Add and verify frontend-origin CORS handling.
- [ ] Persist and retrieve newly created live leads.
- [ ] Wire the frontend advisor to the same persisted lead/context.
- [ ] Add and exercise the frontend feasibility stage.
- [ ] Create orders from accepted quotes in the frontend.
- [ ] Expose the required order state, payment, installation and retry behavior.
- [ ] Wire KYC upload/specimen contract consistently and disclose multipart status.
- [ ] Implement operations assignment, filtering and exception follow-up.
- [ ] Fix analytics response typing and historical/live display.
- [ ] Replace prototype role minting before any multi-user or production-like demo.
- [ ] Add resource ownership enforcement for leads, sessions, KYC, documents and orders.
- [ ] Fix mobile overflow if mobile presentation is in scope.
- [ ] Add a lint script or explicitly document that lint is unavailable.
- [ ] Re-run the complete browser journey against the actual API and capture successful and non-happy-path evidence.

## M. Final sign-off

**NOT READY FOR LIVE DEMONSTRATION.**

The backend has credible isolated prototype behavior: 78 targeted tests pass, the API starts, 25 products load, feasibility states work, quotes are calculated server-side, and order/KYC prerequisite gates reject invalid transitions. Those strengths do not overcome the browser CORS failure, missing frontend journey stages, non-persistent lead creation, non-functional operations controls, analytics contract mismatch, and unsafe prototype authorization boundary.

