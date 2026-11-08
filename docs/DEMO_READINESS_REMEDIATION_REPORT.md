# Accel BizFlow v2.0 — Demo Readiness Remediation Report

Date: 2026-11-08

## Final verdict

**READY WITH DOCUMENTED LIMITATIONS**

The browser can now reach the FastAPI backend, create a persisted lead, start the advisor, call backend recommendations and feasibility, create/accept backend quotes, process the supported synthetic KYC specimen flow, create an order, and operate the persisted order tracker. The backend regression suite and frontend production build pass.

The result is not production-ready. Authentication still uses the existing prototype token issuer, resource ownership is not yet enforced across all customer records, KYC remains filename-based synthetic processing rather than multipart upload, and the frontend operations assignment currently obtains a prototype partner token. These limitations must be disclosed in any demo.

## Finding closure matrix

| ID | Original issue | Change made | Files | Verification | Result |
|---|---|---|---|---|---|
| P0-01 | Missing CORS prevented browser lead submission | Added environment-driven, restricted CORS middleware and documented origins | `backend/app/main.py`, `backend/.env.example` | Browser preflight and browser form submission | Closed |
| P0-02 | Missing feasibility/order/lifecycle frontend stages | Added feasibility screen, order creation after KYC specimen, persisted transition/payment/installation actions | `frontend/src/App.tsx` | Browser lead/advisor path; frontend build | Substantially closed |
| P0-03 | Prototype authentication and missing ownership | Existing role checks remain; no production identity provider or complete ownership model was introduced | Existing `backend/app/api/auth.py`, `backend/app/auth.py` | Existing security suite | Open limitation |
| P1-01 | Leads were not persisted | `LeadRecord` is written transactionally and retrieved from SQLite | `backend/app/api/leads.py` | POST/GET live API check | Closed |
| P1-02 | KYC document route duplicated applicant ID | Body field is optional; URL applicant ID is authoritative | `backend/app/schemas/kyc.py` | Path-only document request contract | Closed |
| P1-03 | Operations control was a toast-only action | Assignment button now calls the partner assignment API and refreshes the queue | `frontend/src/App.tsx` | Build and API route verification | Substantially closed |
| P1-04 | Analytics fields were read from the wrong level | Frontend renders `historical_baseline` fields and “Not available” fallback | `frontend/src/App.tsx`, `frontend/src/api.ts` | Analytics API response inspection | Closed |
| P2-01 | Mobile horizontal overflow | Added global overflow protection and narrow topbar wrapping | `frontend/src/styles.css` | Build; responsive CSS inspection | Substantially closed |
| P2-02 | Human assistance/case controls were misleading | Removed the alert-only claim and changed operations action to a real API-backed assignment | `frontend/src/App.tsx` | Source inspection and build | Partially closed; assistance persistence remains open |

## Exact files changed

- `backend/app/main.py`
- `backend/app/api/leads.py`
- `backend/app/schemas/kyc.py`
- `backend/.env.example`
- `backend/pytest.ini`
- `frontend/src/App.tsx`
- `frontend/src/api.ts`
- `frontend/src/styles.css`
- `docs/DEMO_READINESS_REMEDIATION_REPORT.md`

## Implemented changes

### Browser connectivity

`CORSMiddleware` now reads `ALLOWED_ORIGINS`, defaults to localhost and `127.0.0.1` port 5173, permits the frontend methods, and permits `Authorization`, `Content-Type`, and `Idempotency-Key`. Wildcard origins are not used.

Observed live result:

```text
OPTIONS /api/leads 200 OK
Access-Control-Allow-Origin: http://127.0.0.1:5173
```

### Lead persistence

The existing SQLAlchemy `LeadRecord` is now used by both lead endpoints. A successful POST commits the lead before returning, and GET reads the live record rather than scoring only the historical CSV.

Observed live result:

```text
POST /api/leads 201 Created
GET /api/leads/L-B6A9A7DD 200 OK
```

### Customer journey

- Added a simulated feasibility screen calling `POST /api/feasibility/check`.
- Kept recommendation and quote decisions backend-authoritative.
- Added the feasibility checkpoint before the quote screen.
- KYC document requests now use the path applicant ID without requiring a duplicated body ID.
- After successful specimen processing, the frontend creates an order through `POST /api/orders`.
- The tracker now exposes backend state transitions, payment success/failure/retry, and installation scheduling actions.
- Invalid transitions continue to surface backend error responses.

### Operations and analytics

- Operations assignment calls `POST /api/partner/assignments`, refreshes the queue, and only displays success after the API responds.
- Historical analytics now use the actual nested `historical_baseline` response.
- Missing analytics values display `Not available` rather than fabricated zeroes.

### Responsive behavior

The existing design system was preserved. Narrow viewport rules now wrap the topbar and prevent unintended document-wide horizontal scrolling.

### Test discovery

Added `backend/pytest.ini` with `testpaths = tests`, so the documented backend test suite does not collect the maintenance utility `backend/scripts/patch_test.py`.

## Security limitations remaining

The existing `/api/auth/token` endpoint still accepts caller-supplied identity and role. Existing role authorization checks remain functional, but this is not trusted authentication and must remain local-only with synthetic data. Complete resource ownership enforcement for leads, sessions, KYC cases, documents, quotes and orders is still required before multi-user or production deployment.

KYC remains a synthetic specimen-reference workflow. It does not claim that a filename is a binary customer upload. Feasibility, payment, scheduling and registry integrations remain simulated by design.

## Verification results

| Check | Result |
|---|---|
| `conda run -n torch26 python -m pytest tests -q` | **78 passed** |
| `conda run -n torch26 python -m pytest -q` from `backend` | **78 passed** after `pytest.ini` test discovery configuration |
| `cd frontend; npm run build` | **Passed**, TypeScript and Vite production build |
| FastAPI startup | **Passed** at `127.0.0.1:8000` |
| Health endpoint | **200**, 25 catalogue products |
| Browser frontend startup | **Passed** at `127.0.0.1:5173` |
| Browser lead submission | **Passed**, real POST and navigation to advisor |
| Browser advisor | **Passed to live screen**; Hinglish input was sent to the backend and missing-field follow-up was displayed |
| CORS preflight | **200** with exact frontend origin |
| Live lead persistence | **Passed** with POST then GET |
| Migration SQL generation | **Previously passed** without applying destructive changes |

## Startup instructions

Backend:

```powershell
conda activate torch26
$env:PYTHONPATH = "C:\Users\ACER\Downloads\AirtelSync\backend"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd C:\Users\ACER\Downloads\AirtelSync\frontend
npm install
npm run dev -- --host 127.0.0.1
```

Set `backend\.env` from `.env.example` and restrict `ALLOWED_ORIGINS` to the actual frontend origin in shared environments.

## Demo walkthrough

1. Create a synthetic business lead on the landing screen.
2. Confirm the success toast and advisor navigation.
3. Send a Hinglish business description and complete any missing profile prompts.
4. Review backend recommendations and select a bundle.
5. Check simulated feasibility for Jaipur or an explicitly simulated alternative/survey location.
6. Review and accept the backend-calculated quote.
7. Open a KYC case, grant consent, and process a labelled synthetic specimen.
8. Observe order creation and the persisted order timeline.
9. Advance through the backend state machine, simulate payment success or failure/retry, and schedule installation.
10. Open Operations to view historical baseline separately from live prototype queue records and assign a queue case.

For a non-happy-path demonstration, use `K01_gst_certificate.png`, show the action-required result, then attempt `KYC_VERIFIED` and show the backend rejection rather than claiming activation.

## Remaining limitations and acceptance conditions

- Replace prototype token issuance with trusted demo accounts or OIDC before multi-user use.
- Add resource ownership checks to all customer-owned resources.
- Implement persisted human-assistance request records rather than informational guidance.
- Implement true multipart KYC upload only if the product scope requires customer documents.
- Add browser coverage for the full quote-to-order journey and reviewer workflow.
- Do not describe simulated services as live Airtel coverage, payment, or installation integrations.

