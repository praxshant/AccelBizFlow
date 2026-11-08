"""Security tests: auth, role enforcement, KYC reviewer protection, and token self-escalation."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth import SUPPORTED_ROLES

client = TestClient(app, raise_server_exceptions=False)


def get_token(identity="test-user", role="customer"):
    resp = client.post("/api/auth/token", json={"identity": identity, "role": role})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def test_kyc_review_requires_auth():
    resp = client.post("/api/kyc/cases/K01/review", json={
        "status": "VERIFIED", "reason": "Test", "reviewer_role": "kyc_reviewer"
    })
    assert resp.status_code == 401


def test_kyc_review_requires_reviewer_role():
    token = get_token("cust-01", "customer")
    resp = client.post("/api/kyc/cases/K01/review",
        json={"status": "VERIFIED", "reason": "Test", "reviewer_role": "kyc_reviewer"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 403


def test_kyc_review_accepts_kyc_reviewer_role():
    token = get_token("reviewer-01", "kyc_reviewer")
    client.post("/api/kyc/consent", json={"applicant_id": "SECURITY-TEST-01", "granted": True})
    resp = client.post("/api/kyc/cases/SECURITY-TEST-01/review",
        json={"status": "VERIFIED", "reason": "Security test", "reviewer_role": "kyc_reviewer"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code in (200, 404, 409)


def test_auth_token_endpoint():
    resp = client.post("/api/auth/token", json={"identity": "user1", "role": "sales"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_invalid_token_rejected():
    resp = client.post("/api/kyc/cases/K01/review",
        json={"status": "VERIFIED", "reason": "Test", "reviewer_role": "kyc_reviewer"},
        headers={"Authorization": "Bearer invalid.token.here"}
    )
    assert resp.status_code == 401


def test_unsupported_role_rejected_at_token_creation():
    """The /auth/token endpoint must reject unsupported roles — prevents self-escalation."""
    resp = client.post("/api/auth/token", json={"identity": "attacker", "role": "superuser"})
    assert resp.status_code == 422  # Pydantic validation failure


def test_customer_cannot_escalate_to_admin_via_header():
    """A customer-role JWT must not access partner-only assignment endpoint."""
    token = get_token("cust-02", "customer")
    resp = client.post("/api/partner/assignments",
        json={"case_type": "order", "case_id": "ORD-FAKE", "owner": "partner-01"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 403


def test_sales_cannot_access_kyc_review():
    """Sales role must not be able to review KYC cases."""
    token = get_token("sales-01", "sales")
    client.post("/api/kyc/consent", json={"applicant_id": "SECURITY-TEST-02", "granted": True})
    resp = client.post("/api/kyc/cases/SECURITY-TEST-02/review",
        json={"status": "VERIFIED", "reason": "Sales trying to review"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 403


def test_all_supported_roles_can_be_issued_tokens():
    """Every approved role must be issuable from the prototype token endpoint."""
    for role in sorted(SUPPORTED_ROLES):
        resp = client.post("/api/auth/token", json={"identity": f"user-{role}", "role": role})
        assert resp.status_code == 200, f"Expected 200 for role={role}, got {resp.status_code}"
        assert resp.json()["role"] == role


def test_unaccepted_quote_cannot_create_order():
    """An order must not be created from a non-ACCEPTED quote."""
    profile = {
        "business_type": "retail",
        "segment": "micro",
        "city_tier": 2,
        "employees": 3,
        "sites": 1,
        "gstin_active": False,
    }
    q = client.post("/api/quotes", json={"profile": profile, "items": [{"product_id": "P01", "quantity": 1}]})
    assert q.status_code == 201
    quote_id = q.json()["quote_id"]
    # Do NOT accept the quote — try to create an order directly
    resp = client.post("/api/orders", json={"quote_id": quote_id, "applicant_id": "TEST-ORD-001", "location": "Mumbai"})
    assert resp.status_code == 409


def test_payment_failure_cannot_directly_activate():
    """After payment failure an order must not be directly activatable — it must retry payment first."""
    from uuid import uuid4
    profile = {
        "business_type": "retail",
        "segment": "micro",
        "city_tier": 2,
        "employees": 3,
        "sites": 1,
        "gstin_active": False,
    }
    q = client.post("/api/quotes", json={"profile": profile, "items": [{"product_id": "P01", "quantity": 1}]}).json()
    client.post(f"/api/quotes/{q['quote_id']}/accept")
    order = client.post("/api/orders", json={
        "quote_id": q["quote_id"], "applicant_id": str(uuid4()), "location": "Delhi"
    }).json()
    oid = order["order_id"]
    for state in ("KYC_PENDING", "KYC_VERIFIED", "FEASIBILITY_CLEARED", "PAYMENT_PENDING"):
        client.post(f"/api/orders/{oid}/transition", json={"new_state": state, "reason": "step", "actor": "test"})
    client.post(f"/api/orders/{oid}/payment", json={"outcome": "FAILURE"})
    # Attempt to jump directly to ACTIVATED from PAYMENT_FAILED
    bad = client.post(f"/api/orders/{oid}/transition", json={"new_state": "ACTIVATED", "reason": "cheat", "actor": "test"})
    assert bad.status_code == 409
