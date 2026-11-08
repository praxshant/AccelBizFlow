# Workspace, Advisor and Lead Management Correction

Date: 2026-11-08

## Summary

The targeted UX correction makes the demo workspace selector functional, keeps the advisor in conversational discovery until the customer explicitly chooses the recommendation CTA, and adds persisted lead management.

## Root causes

- The workspace selector only changed a React state value; it did not map roles to destinations or persist the selection.
- Advisor navigation was triggered whenever the backend returned recommendations, so a complete message could leave discovery immediately.
- The lead API only supported create and single-record retrieval. There was no active list, archive operation, safe delete rule, or lead-to-session relationship.

## Implemented behavior

### Workspace switching

The selected demo workspace is stored in `localStorage` and routes to the corresponding experience:

- Customer: onboarding, advisor, catalogue, recommendations, quote, KYC and tracker.
- Sales: sales follow-up queue.
- KYC reviewer: KYC exception queue.
- Partner ops: partner assignment queue.

The selector is explicitly labelled `Demo workspace`; it does not replace authentication or backend authorization.

### Advisor discovery

Advisor messages now remain on the advisor screen. Structured profile updates are shown in the live profile panel, and the `Review eligible products` button is the only transition to recommendations. Quote creation remains behind bundle selection, feasibility and explicit customer actions.

Sessions are created with the active lead ID and restored from the backend when returning to a lead.

### Lead management

The overview now provides:

- `+ New lead`
- Persisted active lead list
- Continue/switch lead
- Archive
- Confirmation-gated permanent delete

Archived leads disappear from the active list but remain in the database. Permanent deletion returns `409` when a lead has linked advisor records, preventing orphaned business history.

## Backend changes

- `GET /api/leads`
- `POST /api/leads/{lead_id}/archive`
- `DELETE /api/leads/{lead_id}`
- `POST /api/advisor/sessions` now accepts an optional `lead_id`
- `GET /api/advisor/sessions?lead_id=...`
- Added backward-compatible SQLite columns for `leads.archived_at` and `conversations.lead_id`

## Tests

- Frontend production build: passed.
- Existing backend regression suite: 78 passed.
- Added lead lifecycle and lead-session isolation tests.
- Manual smoke test: lead creation, list, linked session, archive, safe delete rejection, and unlinked delete all passed.

## Known limitations

The role selector remains a local prototype workspace switch. It does not issue trusted identity credentials. Existing backend role authorization remains authoritative. Quote, KYC and order records are not yet fully linked to lead IDs, so lead status currently reports persisted discovery context and should not be presented as a complete production CRM status model.

## Manual demo

1. Create Lead A and send an incomplete advisor message; verify a targeted follow-up remains in the advisor.
2. Complete the profile; verify the profile panel enables `Review eligible products`.
3. Switch to Overview, create Lead B, continue it, and verify its advisor session is separate.
4. Switch between Customer, Sales, KYC reviewer and Partner ops; verify the page title and queue change.
5. Archive Lead A and verify it disappears from the active list.
6. Attempt to delete the linked Lead A and verify the safe `409` response.
7. Delete an unlinked draft lead after confirmation.
