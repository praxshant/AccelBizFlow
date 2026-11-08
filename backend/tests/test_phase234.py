from fastapi.testclient import TestClient
from uuid import uuid4

from app.main import app


client = TestClient(app)
PROFILE = {
    "business_type": "clinic",
    "segment": "prof",
    "city_tier": 2,
    "employees": 12,
    "sites": 1,
    "gstin_active": True,
}


def test_quote_snapshot_and_idempotent_acceptance():
    response = client.post(
        "/api/quotes",
        json={"profile": PROFILE, "items": [{"product_id": "P02", "quantity": 1}]},
    )
    assert response.status_code == 201
    quote_id = response.json()["quote_id"]
    first = client.post(f"/api/quotes/{quote_id}/accept")
    second = client.post(f"/api/quotes/{quote_id}/accept")
    assert first.status_code == second.status_code == 200
    assert first.json()["accepted_at"] == second.json()["accepted_at"]


def test_advisor_preserves_context_and_validates_profile():
    first = client.post("/api/advisor/message", json={"message": "I run a clinic"})
    assert first.status_code == 200
    assert "segment" in first.json()["missing_fields"]
    cid = first.json()["conversation_id"]
    complete = client.post(
        "/api/advisor/message",
        json={
            "conversation_id": cid,
            "message": "professional, tier 2, 12 employees, 1 site, active GSTIN yes",
        },
    )
    assert complete.status_code == 200
    assert complete.json()["profile"]["employees"] == 12


def test_feasibility_and_consent_gate_document_processing():
    assert client.post("/api/kyc/feasibility", json={"locations": ["Delhi", "remote site"]}).json()["sites"][1]["status"] == "NOT_FEASIBLE"
    applicant = f"TEST-KYC-{uuid4()}"
    payload = {"applicant_id": applicant, "document_type": "gst_certificate", "file_name": "K01_gst_certificate.png"}
    assert client.post("/api/kyc/documents", json=payload).status_code == 403
    assert client.post("/api/kyc/consent", json={"applicant_id": applicant, "granted": True}).status_code == 200
    assert client.post("/api/kyc/documents", json=payload).status_code == 200


def test_reviewer_can_reach_all_kyc_outcomes():
    from app.auth import create_access_token, _secret
    token = create_access_token("test-reviewer", "kyc_reviewer", _secret())
    headers = {"Authorization": f"Bearer {token}"}
    applicant = f"REVIEW-KYC-{uuid4()}"
    client.post("/api/kyc/consent", json={"applicant_id": applicant, "granted": True})
    client.post(
        "/api/kyc/documents",
        json={"applicant_id": applicant, "document_type": "gst_certificate", "file_name": "K01_gst_certificate.png"},
    )
    for status in ("MANUAL_REVIEW", "ACTION_REQUIRED", "VERIFIED"):
        response = client.post(
            f"/api/kyc/cases/{applicant}/review",
            json={"status": status, "reason": "Reviewer decision", "reviewer_role": "kyc_reviewer"},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["status"] == status
