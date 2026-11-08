# Accel BizFlow v2.0 — Locked Implementation Roadmap

> **Document status: LOCKED BASELINE**
>
> This roadmap is the implementation source of truth for the Accel BizFlow case competition project. Do not edit, reorder, remove, reinterpret, or silently expand any decision in this file. Changes may be made only after an explicit instruction from the project owner. Evidence, test results, and implementation progress belong in code, tests, reports, or other project documentation—not by rewriting this baseline.

**Version:** 1.0  
**Created:** 2026-11-07  
**Product:** Accel BizFlow v2.0  
**Case:** YTL Hackathon 2026 — Enterprise Track A, Project Udyam Digital  
**Primary objective:** Build and demonstrate a mobile-first, multilingual MSME acquisition and activation journey that improves commercial conversion, onboarding, and fulfilment while preserving human assistance for complex or high-value accounts.

---

## 1. Governing strategy

Accel Business currently activates **368 of 5,000 synthetic SMB leads (7.36%)**. The principal problem is not a single missing AI feature; it is a fragmented journey:

1. Needs discovery depends on visits and sales availability.
2. Quotes are slow, opaque, and difficult to compare.
3. KYC is paper-heavy and disconnected from the customer journey.
4. Feasibility and installation risk are discovered too late.
5. Customers lack order visibility and call repeatedly for status.

### Strategic recommendation

Build **Accel BizFlow**, a connected commercial and operational platform that:

- discovers business needs conversationally;
- recommends only eligible catalogue products;
- creates transparent, configurable quotes;
- checks network feasibility before commitment;
- automates document extraction and registry validation;
- coordinates payment, installation, and activation;
- routes valuable or exceptional cases to people.

### Core thesis

> **Accel loses MSME customers through a fragmented journey; BizFlow converts more demand by fixing commercial friction, automating onboarding, and connecting digital acquisition to physical fulfilment.**

### Non-negotiable architecture principle

> **The LLM extracts and explains. Deterministic backend services decide.**

The LLM may interpret natural language, extract structured fields, ask follow-up questions, and explain verified outcomes. It must not approve products, calculate authoritative prices, verify legal identity, override eligibility, reject KYC autonomously, or activate an order.

---

## 2. Source of truth and evidence boundaries

### Supplied source material

- `YTL_TrackA_Udyam_Digital_Data/README.md`
- `YTL_TrackA_Udyam_Digital_Data/product_catalogue.csv` — 25 products
- `YTL_TrackA_Udyam_Digital_Data/smb_leads.csv` — 5,000 synthetic leads
- `YTL_TrackA_Udyam_Digital_Data/mock_gstin_registry.csv` — 3,534 synthetic records
- `YTL_TrackA_Udyam_Digital_Data/mock_udyam_registry.csv` — 2,723 synthetic records
- `YTL_TrackA_Udyam_Digital_Data/kyc_documents/` — 47 specimen images, 12 applicants
- `6ad9d4887d445_airtel_sync/Airtel_SYNC_Case.pdf`
- `6ad9d4887d445_airtel_sync/Submission Template_Sync.pptx`
- Owner-provided **ACCEL BIZFLOW — FINAL SOLUTION BLUEPRINT v2.0**

All provided businesses, people, identifiers, documents, and figures are fictional and synthetic. The prototype must never imply that the mock registries, coverage service, payment service, or installation scheduler are live production integrations.

### Evidence labels

Every business claim in the presentation and documentation must be labelled as one of:

- **Case data:** directly computed or stated from supplied synthetic data.
- **Prototype behaviour:** demonstrated by the implemented system.
- **Scenario assumption:** an explicit model input such as 56% quote acceptance.
- **Illustrative prototype value:** midpoint pricing or simulated service output.
- **To validate:** requires real commercial, coverage, operational, legal, or customer evidence.

Never present scenario outputs as observed results.

---

## 3. Locked product and customer strategy

| Decision | Locked baseline |
|---|---|
| Product name | Accel BizFlow v2.0 |
| Product category | MSME digital acquisition and onboarding |
| Primary customer | Professional offices |
| High-value customer | Small multi-site businesses |
| Conditional customer | Micro retail and services |
| Assisted segment | Small manufacturers |
| Primary user | MSME owner |
| Secondary users | Sales executives, channel partners, KYC reviewers |
| Frontend | React + Vite + TypeScript |
| Styling | Tailwind CSS |
| Backend | Python + FastAPI |
| Database | SQLite initially; schema migration-ready for PostgreSQL |
| ORM | SQLAlchemy |
| Validation | Pydantic |
| LLM | One provider behind an abstraction layer, structured output |
| OCR | Local PaddleOCR + OpenCV |
| Recommendation | Deterministic eligibility and dependency engine |
| Pricing | Central configurable rate card with versioned quotes |
| Feasibility | Clearly labelled simulated coverage API |
| KYC | Local OCR + mock GSTIN/Udyam registry validation |
| Orders | Explicit state-based workflow with append-only events |
| Analytics | Pandas; transparent lead-scoring baseline with scikit-learn as stretch |
| Testing | Pytest |
| Packaging | Docker |
| Submission | Working prototype, 3-minute demo, architecture diagram, business case ≤10 slides, one-page privacy/security note |

### Segment strategy

- **Professional offices:** digital-first journey; target clinics, CA firms, coaching centres; prioritise reliable connectivity, cloud email, storage, and security.
- **Multi-site businesses:** high-value assisted acquisition; target chains with multiple locations; prioritise one bill, central management, CCTV, failover, and SD-WAN.
- **Manufacturers:** specialist-assisted journey; prioritise dedicated bandwidth, security, IoT, and ERP access.
- **Micro retail:** self-service and price-sensitive journey; scale only if measured acquisition and servicing economics meet the approved contribution/payback gate.

### Human-assistance policy

Human help must be visible and reachable at every stage. Route high-value multi-site accounts, manufacturers, KYC exceptions, abandoned quotes, payment failures, and installation delays to the partner/sales queue. The product augments the sales force; it does not replace it.

---

## 4. Locked business facts and scenario model

### Baseline funnel

| Stage | Count | Conversion from previous |
|---|---:|---:|
| Leads generated | 5,000 | — |
| Contacted | 3,406 | 68% |
| Needs assessed | 1,974 | 58% |
| Quote accepted | 861 | 44% |
| KYC complete | 588 | 68% |
| Activated | 368 | 63% |

Additional supplied case facts:

- Average lead-to-activation time: **17.6 days**.
- Average customer status chases: **3**.
- Blended baseline CAC: approximately **INR 15,000 per activated SMB**.
- GSTIN leads activate at approximately **9.6%** versus **2.0%** without GSTIN.
- Six-month churn field: **56 of 368 (15.2%)**, treated as synthetic supplied data.

### Recorded loss buckets

| Funnel loss | Count | Main recorded reasons |
|---|---:|---|
| Lead -> Contact | 1,594 | Unreachable, not interested, invalid number |
| Contact -> Assessment | 1,432 | No time for visit, locked-in provider, visit not scheduled, mobile-only need |
| Assessment -> Quote | 1,113 | Price, competitor, quote complexity, quote delay, waiting |
| Quote -> KYC | 273 | Missing documents, paperwork time, signatory unavailable, mismatched details |
| KYC -> Activation | 220 | Installation delay, cancellation, fibre infeasibility, payment failure |

Of the 1,113 quote-stage losses, **621 (55.8%)** are price/competitor-coded and **385 (34.6%)** are complexity/delay-coded. Therefore, the product must combine price-fit, transparent packaging, immediate quoting, and relevant recommendations. AI discovery alone is not the solution.

### Segment evidence

| Segment | Leads | Activated | Conversion | CAC |
|---|---:|---:|---:|---:|
| Micro retail | 2,709 | 110 | 4.06% | INR 20,007 |
| Professional offices | 1,247 | 138 | 11.07% | INR 10,695 |
| Multi-site businesses | 755 | 83 | 10.99% | INR 15,614 |
| Manufacturers | 289 | 37 | 12.80% | INR 15,324 |

Multi-site and manufacturing customers represent approximately **71.2% of activated monthly value proxy** while contributing only approximately **20.9% of leads**. This is a median-value proxy, not recognised revenue or profit.

### Scenario model

Use the following only as an explicit projection:

| Stage | Baseline | Base scenario | Upside scenario |
|---|---:|---:|---:|
| Quote acceptance | 43.6% | 56% | 56% |
| Quote-to-KYC completion | 68.3% | 85% | 85% |
| KYC-to-activation | 62.6% | 62.6% | 75% |
| Activations from 5,000 leads | 368 | ~588 | ~705 |
| Lead-to-activation | 7.36% | 11.8% | 14.1% |

Under the illustrative assumption of INR 10,00,000 quarterly platform cost and unchanged acquisition spend:

| Scenario | Activations | Illustrative all-in CAC |
|---|---:|---:|
| Current | 368 | INR 17,771 |
| Base | 588 | INR 11,121 |
| Upside | 705 | INR 9,280 |

The base and upside numbers are not prototype results. The upside requires improvement in post-KYC fulfilment, not only KYC automation.

---

## 5. Target end-to-end customer journey

1. **Discover and start:** website, referral, QR, field sales, or WhatsApp creates a lead and mobile session.
2. **Understand the business:** advisor collects only missing business, location, size, language, current setup, budget, and requirement fields.
3. **Validate eligibility:** deterministic engine filters catalogue products by segment, city tier, employees, sites, GSTIN, dependencies, quantity, and unit.
4. **Check feasibility:** selected connectivity is classified as available, alternative available, survey required, or not feasible.
5. **Generate and accept quote:** customer sees eligible options, recurring and one-time charges, quantities, terms, validity, and optional add-ons.
6. **Complete KYC:** explicit consent, required document upload, local OCR, registry lookup, cross-document checks, and exception handling.
7. **Confirm payment and create order:** simulated payment with visible retry/failure behaviour.
8. **Schedule installation:** simulated partner/slot assignment, indicative ETA, delay updates, and escalation.
9. **Activate and hand over:** activation is recorded only after the relevant service confirmation; customer receives confirmation, billing, and support information.

Alternative route at every stage: request human assistance or enter an exception queue.

---

## 6. Functional scope

### 6.1 Lead intake and business profile

Persist:

- business type, segment, city, state, PIN, and city tier;
- employee count, site count, turnover band;
- GSTIN/Udyam availability and identifiers;
- preferred language;
- current internet/provider and monthly telecom spend;
- needs, products of interest, contact role, and source.

Returning customers must not repeat already-validated discovery fields.

### 6.2 AI business advisor

Initial languages: Hindi and English, with a design extensible to regional languages.

Required structured output:

```json
{
  "business_profile": {
    "segment": "professional",
    "business_type": "clinic",
    "city": "Jaipur",
    "city_tier": 2,
    "employees": 12,
    "sites": 1,
    "gstin_available": true
  },
  "requirements": [
    "reliable_connectivity",
    "business_email",
    "endpoint_security"
  ],
  "missing_fields": [],
  "next_action": "generate_recommendations"
}
```

The advisor is adaptive, not a rigid questionnaire. All extracted values must be schema-validated and passed to backend rules.

### 6.3 Catalogue and eligibility engine

Import all 25 products from `product_catalogue.csv`. Enforce:

1. target segment;
2. city tier;
3. minimum employees;
4. minimum sites;
5. active GSTIN requirement;
6. `requires_one_of` companion dependency;
7. valid quantity and unit.

The engine returns up to three valid configurations:

- **Essential:** minimum needs;
- **Recommended:** best match;
- **Advanced:** justified add-ons.

No invalid product or bundle may reach quote generation. The LLM cannot override a failed rule.

### 6.4 Pricing and checkout

Implement:

- product quantities and units;
- per-site, per-line, per-user, per-device, per-account, per-camera, and per-vehicle pricing;
- recurring monthly charges;
- one-time setup charges;
- optional add-ons;
- product-specific minimum contracts;
- quote validity and acceptance;
- order creation;
- quote idempotency.

For the prototype, default price is the midpoint:

`(price_min + price_max) / 2`

This is illustrative only. Prices must come from a versioned rate card, remain within configured bounds, and record authorised overrides in the audit trail.

Quote must show product descriptions, quantity, line items, recurring total, setup total, contract terms, validity, eligibility result, and the longest commitment without hiding shorter product terms.

### 6.5 Feasibility engine

Use a seeded, clearly labelled simulated coverage table. Inputs:

- installation PIN/address;
- city/state;
- selected connectivity;
- number of sites.

Outputs:

- `AVAILABLE`;
- `ALTERNATIVE_AVAILABLE`;
- `SURVEY_REQUIRED`;
- `NOT_FEASIBLE`.

Store timestamp and validity window. Never claim real network coverage.

### 6.6 Smart KYC

Required document types:

- GST certificate;
- Udyam certificate;
- address proof;
- authorised signatory ID.

Pipeline:

1. purpose-specific consent;
2. upload;
3. local OCR and extraction;
4. format and confidence checks;
5. mock GSTIN lookup;
6. mock Udyam lookup;
7. cross-document validation;
8. final status.

Statuses:

- `VERIFIED`;
- `ACTION_REQUIRED`;
- `MANUAL_REVIEW`;
- `REJECTED`.

Validate legal/trade identity, address/PIN/state, registry status, document dates, signatory identity, and authorisation. Use **2026-07-15** as the supplied reference date for freshness checks. Accept the synthetic GSTIN `X` convention and Udyam district code `00`.

Low OCR confidence must result in re-upload/action-required or manual review, never automatic rejection.

### 6.7 Orders and tracker

Implement explicit transitions, not hardcoded labels:

```text
DRAFT
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

Exception states:

```text
KYC_ACTION_REQUIRED
KYC_MANUAL_REVIEW
KYC_REJECTED
FEASIBILITY_SURVEY_REQUIRED
FEASIBILITY_UNAVAILABLE
PAYMENT_FAILED
INSTALLATION_BLOCKED
CANCELLED
```

Each event records actor, previous state, new state, timestamp, reason/event code, and optional next action. Customer language must explain the state and next step. Delays must be visible, with revised ETA and escalation—not hidden.

### 6.8 Partner/sales dashboard

Recommended after the core journey:

- high-value multi-site leads;
- manufacturing enquiries;
- abandoned quotes;
- KYC exceptions;
- payment failures;
- installation delays;
- callback queue;
- assignment, attribution, and status.

### 6.9 Analytics and lead prioritisation

Mandatory descriptive analytics:

- funnel and stage conversion;
- segment conversion;
- source conversion and CAC;
- drop reasons;
- bundle combinations;
- monthly bundle value;
- churn and NPS.

Stretch predictive score:

`P(activation) x expected monthly value x retention factor`

Use point-in-time features only. Do not use activation dates, final outcome, drop reason, or churn as scoring inputs. The score is a relative prioritisation aid, not true LTV or profit.

---

## 7. Technical architecture and data model

### Architecture shape

Use a modular monolith:

```text
React/Vite/TypeScript frontend
  Customer PWA: advisor, catalogue, quote, KYC, tracker
  Partner view: queue, assignment, exceptions
        |
FastAPI REST backend
  Authentication/session management/input validation
  Advisor service
  Catalogue/eligibility service
  Pricing/quote service
  Feasibility service
  KYC service
  Order/event service
  Analytics/lead scoring
  Partner service
        |
SQLite + SQLAlchemy
  profiles, catalogue, quotes, documents, orders, audit events
        |
Local OCR | mock registries | simulated coverage/payment/scheduling
```

Do not introduce Redis, Celery, Kubernetes, LangGraph, vector stores, microservices, or multiple agents unless an explicit new requirement is approved.

### Core entities

`leads`, `business_profiles`, `advisor_sessions`, `advisor_messages`, `products`, `pricing_versions`, `recommendation_runs`, `recommendation_items`, `quotes`, `quote_items`, `feasibility_checks`, `consents`, `kyc_cases`, `kyc_documents`, `kyc_validation_results`, `orders`, `order_events`, `partner_cases`, `lead_scores`, `audit_events`, plus read-only `gstin_registry` and `udyam_registry`.

### Data invariants

1. Accepted quotes preserve the pricing version used at creation.
2. Document binaries are separated from metadata and kept in private storage.
3. Order events are append-only.
4. Audit trail is independent of conversational history.
5. Registry tables are read-only and indexed by identifier.
6. Duplicate quote, payment, and order requests are idempotent.
7. Raw identifiers and document contents never appear in ordinary logs.

### API surface

| Area | Endpoints |
|---|---|
| Leads/advisor | `POST /api/leads`, `GET /api/leads/{id}`, `POST /api/advisor/sessions`, `POST /api/advisor/sessions/{id}/messages`, `GET /api/advisor/sessions/{id}` |
| Catalogue/quotes | `GET /api/catalog/products`, `GET /api/catalog/products/{id}`, `POST /api/recommendations/evaluate`, `POST /api/feasibility/check`, `POST /api/quotes`, `GET /api/quotes/{id}`, `PATCH /api/quotes/{id}/items`, `POST /api/quotes/{id}/accept` |
| KYC/orders | `POST /api/kyc/cases`, `POST /api/kyc/cases/{id}/consent`, `POST /api/kyc/cases/{id}/documents`, `GET /api/kyc/cases/{id}`, `POST /api/kyc/cases/{id}/review`, `POST /api/orders`, `GET /api/orders/{id}` |
| Operations/analytics | `GET /api/partner/queue`, `GET /api/analytics/funnel` |

All simulated integrations must be explicitly labelled in the UI and demo.

---

## 8. Implementation phases and dependencies

### Phase 0 — Data validation and project foundation

**Dependency:** none  
**Output:** reproducible analysis and validated source-data contract.

- Set up repository structure, environment, `.env.example`, and `.gitignore`.
- Copy or reference only synthetic competition data.
- Load all CSV schemas and validate row counts.
- Reproduce funnel, segment, source, drop-reason, CAC, bundle, churn, NPS, and lead-time metrics.
- Load all 25 product records.
- Map eligibility fields, units, dependencies, and install days.
- Record assumptions separately from facts.

**Exit gate:** analysis can be rerun and reproduces the locked baseline metrics without manual spreadsheet edits.

### Phase 1 — Catalogue, eligibility, and dependency engine

**Dependency:** Phase 0  
**Output:** valid recommendations without AI.

- Define typed product, business-profile, bundle, and eligibility schemas.
- Implement city-tier, segment, employee, site, GSTIN, quantity, and unit checks.
- Implement `requires_one_of` as a hard same-bundle constraint.
- Return Essential/Recommended/Advanced configurations.
- Add unit tests for valid and invalid combinations.
- Ensure no rule can be bypassed by LLM output.

**Exit gate:** a submitted business profile returns only eligible configurations; P10 fails for three sites with five employees; dependent products fail without a companion.

### Phase 2 — Pricing, bundles, quotes, and checkout

**Dependency:** Phase 1  
**Output:** complete deterministic quotation backend.

- Implement versioned rate-card schema.
- Apply midpoint default prices within catalogue ranges.
- Calculate quantity-based recurring and setup totals.
- Preserve product-level contract terms and longest commitment.
- Support add/remove/toggle add-ons and live recalculation.
- Generate, retrieve, modify, and accept quotes.
- Add quote arithmetic and idempotency tests.

**Exit gate:** every quote reconciles 100% from line items; no ineligible item can be quoted; accepted quote preserves its pricing version.

### Phase 3 — Conversational advisor

**Dependency:** Phases 1–2  
**Output:** adaptive multilingual discovery connected to real rules.

- Add provider abstraction and structured-output schema.
- Implement missing-field detection and adaptive follow-ups.
- Support Hindi and English, including Hinglish test input.
- Send structured, masked data only where possible.
- Explain verified recommendation reasons in plain language.
- Add prompt/output allowlists and backend authorisation.

**Exit gate:** advisor creates a valid profile, asks only necessary questions, and invokes deterministic recommendation/pricing services rather than deciding itself.

### Phase 4 — Feasibility and Smart KYC

**Dependency:** Phase 2; advisor integration may be parallel after profile schemas are stable  
**Output:** trustworthy verification and exception workflow.

- Build seeded simulated feasibility API with validity window.
- Implement consent screen and purpose tracking.
- Implement upload metadata and private file handling.
- Integrate local PaddleOCR/OpenCV extraction.
- Import read-only mock GSTIN/Udyam registries.
- Implement cross-document checks and four KYC outcomes.
- Process all 47 supplied images across 12 applicants.
- Route low confidence and mismatch cases to action-required/manual review.

**Exit gate:** consent precedes processing; all specimen images produce documented outcomes; no low-confidence OCR auto-rejects; no raw identity data is sent unnecessarily to the LLM or logs.

### Phase 5 — Order orchestration and tracker

**Dependency:** Phases 2 and 4  
**Output:** quote-to-activation workflow.

- Create order only from accepted quote and valid prerequisite state.
- Implement simulated payment and retry/failure.
- Implement explicit state transition authorisation.
- Record append-only order events.
- Implement installation slot simulation and ETA.
- Expose customer tracker and exception escalation.

**Exit gate:** happy path and failure paths are persisted, auditable, and understandable to a customer.

### Phase 6 — Partner/sales dashboard and analytics

**Dependency:** Phases 0 and 5  
**Output:** human-assisted operating layer.

- Build funnel and segment analytics views.
- Add priority routing and transparent score explanation.
- Show abandoned quotes, high-value leads, KYC exceptions, payment failures, and installation delays.
- Add assignment, attribution, and callback actions.
- Ensure point-in-time features and no outcome leakage.

**Exit gate:** an operator can find, assign, and resolve each major exception category.

### Phase 7 — Integration, competition hardening, and submission

**Dependency:** Phases 1–6  
**Output:** submission-ready MVP.

- Run the complete customer journey with at least 15 authored scenarios.
- Run all 47 KYC specimens.
- Test accessibility, responsive mobile layout, multilingual flows, and error states.
- Verify security and privacy controls.
- Capture working prototype screenshots.
- Produce architecture diagram.
- Produce one-page privacy/security note.
- Produce business case deck with no more than 10 slides.
- Record demo of no more than 3 minutes.
- Run final smoke test from clean startup instructions.

**Exit gate:** all mandatory acceptance criteria pass and the demo includes one non-happy-path example.

---

## 9. Definition of done and mandatory quality gates

| Component | Done when |
|---|---|
| Business profile | Extracted, validated, persisted, and reusable |
| Advisor | Creates structured requirements and asks only necessary follow-ups |
| Catalogue | All 25 products imported correctly |
| Eligibility | Every mandatory rule and dependency enforced |
| Recommendations | Only valid products reach quote engine |
| Pricing | Every quote reconciles to item-level charges |
| Feasibility | Available, alternative, survey, and unavailable states work |
| KYC | Documents extracted, cross-checked, and assigned a justified status |
| Consent | Required consent blocks processing until recorded |
| Orders | Validated state transitions are persisted |
| Tracker | Customer sees current and previous events, next action, and delays |
| Partner dashboard | Exceptions are visible and assignable |
| Security | No raw identifiers/document content in unnecessary logs or LLM requests |

Hard quality gates:

- **Ineligible quotations:** zero.
- **Quote arithmetic reconciliation:** 100%.
- **Low-confidence OCR:** never automatic rejection.
- **Human handoff:** accessible at every stage.
- **Order auditability:** every transition has actor, prior/new state, timestamp, and reason.
- **Synthetic integration clarity:** simulated services visibly labelled.

---

## 10. Required validation scenarios

At minimum, implement and test:

1. Single-location kirana receives eligible micro bundle.
2. Dental clinic with 12 employees receives professional-office recommendation.
3. Three-outlet restaurant receives multi-site recommendation.
4. Tier-2 manufacturer receives specialist-assisted option.
5. Customer without GSTIN cannot receive GSTIN-required products.
6. Three sites and five employees cannot receive P10 Managed SD-WAN.
7. Dependency product without connectivity companion is rejected.
8. Fibre unavailable produces alternative or survey outcome.
9. Add-on toggle reprices quote correctly.
10. Suspended/cancelled GST registration blocks relevant products.
11. Unreadable document becomes action-required.
12. Address mismatch becomes manual review.
13. Address proof older than 90 days triggers date validation.
14. Hinglish response creates correct structured profile.
15. Installation delay updates tracker and partner queue.
16. Payment failure provides retry and does not falsely activate.
17. Duplicate quote/order request does not create duplicates.
18. Customer can request human assistance at any stage.

These are the project’s validation scenarios, not the judges’ private test pack or answer key.

---

## 11. KPI framework and pilot

### Primary KPIs

| KPI | Baseline | Scenario target | Owner |
|---|---:|---:|---|
| Lead-to-activation | 7.36% | 11.8% base / 14.1% upside | SMB Growth |
| Quote acceptance | 43.6% | 56% | Product/Sales |
| Quote-to-KYC completion | 68.3% | 85% | KYC Operations |
| KYC-to-activation | 62.6% | 75% upside | Fulfilment |
| All-in CAC | INR 15,053 before platform cost | ~INR 9,300 upside model | Finance |

### Guardrails

- KYC false-rejection rate: proposed threshold **≤1%** in a sufficiently sized adjudicated pilot.
- Ineligible quotations issued: **0**.
- Customer status-chasing calls: reduce from **3** to below **1**.
- Also monitor median and average activation time, installation delays over 21 days, payment recovery, and six-month churn.

### Pilot design

- Segments: professional offices and multi-site businesses.
- Geography: one or two cities selected after city-level lead-volume and installation-coverage analysis.
- Control: existing discovery, quoting, and onboarding.
- Treatment: BizFlow discovery, eligibility, transparent quote, and integrated onboarding.
- Primary test: quote acceptance.
- Secondary tests: KYC completion, post-KYC activation, quote processing time, status calls, feasibility failures.
- Initial sample planning: approximately 300 assessed leads per arm for a 44% to 56% quote-acceptance test, subject to recruitment feasibility.
- Do not claim statistically proven activation lift from the prototype.

### Kill conditions

1. **Price competitiveness:** eligible offers remain unaffordable or uncompetitive.
2. **Installation capacity:** accepted orders cannot be fulfilled within a credible SLA.
3. **Micro-retail economics:** self-service does not reduce incremental acquisition and servicing cost toward the approved contribution/payback threshold.

---

## 12. Privacy, security, and trust requirements

The prototype is compliance-oriented by design; it is not a legal certification.

- Show clear notice and purpose-specific consent before KYC.
- Request only necessary documents and fields.
- Keep document binaries private and separate from metadata.
- Perform OCR locally.
- Send masked structured fields—not raw identity documents—to the LLM.
- Use role-based access for customers, reviewers, and sales.
- Mask identifiers and exclude document contents from logs.
- Use configurable purpose-based retention and deletion.
- Keep consent, access, verification decisions, and state transitions auditable.
- Treat customer text and OCR output as untrusted input; never interpret it as system instructions.
- Use schema validation, output allowlists, restricted tool access, and backend authorisation.
- Never commit API keys, secrets, or uploaded identity documents.
- Use only synthetic competition specimens in the repository.

---

## 13. Submission narrative and presentation lock

The submission story must be one argument, not a feature catalogue.

| Slide | Locked action title | Required proof |
|---:|---|---|
| 1 | Only 7.36% of SMB leads activate because acquisition and onboarding are fragmented | Funnel, five loss buckets, opportunity |
| 2 | Professional offices drive digital conversion, while multi-site businesses drive activated value | Segment economics, value proxy, differentiated strategy |
| 3 | BizFlow connects discovery, eligible bundles, checkout, and activation in one journey | Real prototype screenshots and customer flow |
| 4 | GenAI understands customer needs while deterministic services control commercial decisions | Architecture and AI boundary |
| 5 | Upfront feasibility and verified KYC remove avoidable onboarding and fulfilment failures | KYC, feasibility, security, exception path |
| 6 | BizFlow combines a connected digital journey with existing human sales and partner networks | Operating model and verified competitor comparison |
| 7 | A staged conversion improvement can produce 588–705 activations per 5,000 leads under explicit assumptions | Business case, CAC sensitivity, pilot, risks, rollout |

Competitor comparisons with JioBusiness, Tata Tele Business Services, and Vi Business must be researched and verified before asserting any capability gap.

### Three-minute demo sequence

| Time | Demo |
|---|---|
| 0:00–0:20 | Business problem and customer |
| 0:20–0:55 | Advisor discovers requirements |
| 0:55–1:25 | Eligible bundle and dynamic quotation |
| 1:25–2:05 | Feasibility and KYC |
| 2:05–2:35 | Order tracking and installation update |
| 2:35–3:00 | Partner dashboard and exception handling |

Include one non-happy path, preferably an ineligible SD-WAN recommendation blocked by rules or a mismatched document routed to manual review.

---

## 14. Recommended project structure

```text
accel-bizflow/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── advisor/
│   │   ├── quotation/
│   │   ├── kyc/
│   │   ├── tracker/
│   │   └── partner/
│   └── package.json
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   │   ├── advisor/
│   │   │   ├── catalogue/
│   │   │   ├── eligibility/
│   │   │   ├── pricing/
│   │   │   ├── feasibility/
│   │   │   ├── kyc/
│   │   │   ├── orders/
│   │   │   └── lead_scoring/
│   │   ├── database/
│   │   └── main.py
│   ├── tests/
│   └── requirements.txt
├── data/
├── analytics/
├── uploads/
├── docs/
├── demo/
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

## 15. What is frozen versus what must be validated

### Frozen for development

- Accel BizFlow name and product proposition.
- Professional-office digital-first and multi-site high-value priorities.
- React/TypeScript + FastAPI + SQLite baseline.
- Modular monolith.
- Deterministic eligibility, dependency, pricing, and state logic.
- LLM boundary.
- Local OCR and mock registry approach.
- Simulated feasibility/payment/scheduling integrations.
- Seven-slide narrative and three-minute demo sequence.
- Phase order and quality gates in this roadmap.

### Must remain explicitly open

- Approved production selling prices and margins.
- Actual customer willingness to pay.
- Actual network coverage and installation capacity.
- Real retention/deletion policy and operational security approval.
- Platform operating cost at scale.
- Whether micro-retail expansion clears the contribution/payback gate.
- Competitor capabilities at the time of presentation.
- Pilot duration and city selection.

New evidence may be recorded in supporting documents, but this locked baseline must not be changed without explicit owner instruction.

---

## 16. Immediate first milestone

Begin implementation here and do not start with conversational AI:

1. Create `analytics/lead_analysis.py` and reproduce locked business metrics.
2. Import all 25 catalogue products.
3. Define typed eligibility and dependency schemas.
4. Implement deterministic product validation.
5. Implement quantity-based quote calculations.
6. Write tests for valid and invalid bundle combinations.

### First milestone acceptance

Given a business profile, the backend returns only eligible product configurations with correctly calculated prices. Ineligible dependencies, GSTIN requirements, city tiers, employee thresholds, site thresholds, quantities, and units are enforced by backend logic.

Only after this milestone passes should the conversational advisor be connected to the recommendation and quote services.

---

## 17. Change-control rule

This file is intentionally locked. If a change is needed, the project owner must provide an explicit instruction identifying:

1. the section or decision to change;
2. the replacement decision;
3. the reason or new evidence;
4. whether the change affects implementation, metrics, demo, or submission scope.

Until that instruction is received, implementation must follow this roadmap exactly. 
