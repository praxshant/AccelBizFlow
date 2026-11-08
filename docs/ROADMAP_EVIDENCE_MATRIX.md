# Accel BizFlow Roadmap Evidence Matrix

Date: 2026-11-08

## Current verdict

**Substantial prototype with the primary customer happy path verified.** The application is not production-ready or fully roadmap-complete because authentication, ownership, real uploads, full analytics, and several competition-hardening gates remain.

## Verified in this pass

| Area | Evidence | Status |
|---|---|---|
| Catalogue foundation | `GET /health` reports 25 products | Verified |
| Advisor retention | Context-aware short answers now update the stored profile; focused tests pass | Verified |
| Customer discovery gate | Advisor stays in discovery; recommendations require an explicit CTA | Verified |
| Lead management | List, lead-linked sessions, archive, safe delete, and isolation tests | Verified |
| Sales workspace | `GET /api/sales/queue` returns persisted lead records | Verified |
| KYC reviewer workspace | `GET /api/partner/queue?case_type=kyc` returns only KYC exceptions | Verified |
| K07 OCR | `K07_gst_certificate.png` returned `VERIFIED`, confidence `0.77` | Verified |
| Human assistance | Assistance requests persist and appear in the Partner Ops queue | Verified |
| Multipart KYC | PNG/JPEG upload endpoint stores privately for processing and removes the temporary file | Verified |
| KYC order gate | KYC must be `VERIFIED` before `KYC_VERIFIED` transition | Verified |
| Order happy path | Completed through `ACTIVATED` with all ten expected events | Verified |
| Backend regression | 83 tests passed | Verified |
| Frontend build | TypeScript/Vite production build passed | Verified |

## K07 happy-path evidence

The clean synthetic journey used an eligible `P01` quote and applicant `K07-e2c4a4b1`.

```text
K07_DOCUMENT 200
status: VERIFIED
GSTIN: 07CPCX*** active and verified in registry
confidence: 0.77

ORDER_ID: 321679f4-bfcf-4f31-a6d7-844cb478122c
final status: ACTIVATED
events:
QUOTE_ACCEPTED
KYC_PENDING
KYC_VERIFIED
FEASIBILITY_CLEARED
PAYMENT_PENDING
PAYMENT_CONFIRMED
INSTALLATION_SCHEDULED
INSTALLATION_IN_PROGRESS
SERVICE_INSTALLED
ACTIVATED
```

## Remaining roadmap gaps

| Area | Remaining work |
|---|---|
| Quote configuration | Quantity editing, add/remove add-ons, validity and contract-term UX are not complete |
| KYC | Remaining document types, cross-document validation, all 47 specimens, and reviewer actions need broader verification |
| Feasibility | All four outcomes need browser evidence |
| Operations | Assignment persistence and exception resolution UI need dedicated verification |
| Analytics | Source conversion/CAC, drop reasons, bundles, monthly value, churn and NPS are not fully surfaced |
| Security | Prototype token issuance and incomplete resource ownership remain local-demo limitations |
| Competition hardening | Full specimen matrix, accessibility, multilingual, privacy note, architecture diagram and submission artifacts still need validation |

## Files changed for this pass

- `backend/app/services/advisor/conversation.py`
- `backend/app/schemas/advisor.py`
- `backend/app/services/analytics.py`
- `backend/app/api/operations.py`
- `frontend/src/App.tsx`
- `backend/tests/test_lead_management.py`
