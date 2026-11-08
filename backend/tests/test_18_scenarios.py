"""
End-to-End Test Suite covering the 18 Blueprint Scenarios for Accel BizFlow.
"""
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.auth import create_access_token, _secret
from app.schemas.eligibility import BusinessProfile, RecommendationRequest

client = TestClient(app, raise_server_exceptions=False)


def auth_headers(identity="reviewer-01", role="kyc_reviewer"):
    token = create_access_token(identity, role, _secret())
    return {"Authorization": f"Bearer {token}"}


# 1. Micro retail sole proprietor, 1 site, 3 staff, no GSTIN
def test_scenario_01_micro_retail_no_gstin():
    profile = BusinessProfile(
        business_type="retail",
        segment="micro",
        city_tier=2,
        employees=3,
        sites=1,
        gstin_active=False,
    )
    rec = app.state.eligibility.recommend(RecommendationRequest(profile=profile))
    assert len(rec.eligible_products) > 0
    # GSTIN-required products must be in ineligible_products
    gstin_req_ids = [d.product.product_id for d in rec.ineligible_products if d.product.requires_gstin]
    assert len(gstin_req_ids) > 0


# 2. Micro retail with active GSTIN
def test_scenario_02_micro_retail_with_gstin():
    profile = BusinessProfile(
        business_type="retail",
        segment="micro",
        city_tier=1,
        employees=5,
        sites=1,
        gstin_active=True,
    )
    rec = app.state.eligibility.recommend(RecommendationRequest(profile=profile))
    assert len(rec.eligible_products) > 0


# 3. Professional office, Tier 1, 15 staff, active GSTIN
def test_scenario_03_professional_office():
    profile = BusinessProfile(
        business_type="office",
        segment="prof",
        city_tier=1,
        employees=15,
        sites=1,
        gstin_active=True,
    )
    rec = app.state.eligibility.recommend(RecommendationRequest(profile=profile))
    assert len(rec.bundles) == 3
    assert any(b.name == "recommended" and len(b.product_ids) >= 2 for b in rec.bundles)


# 4. Small multi-site business, 3 sites, 20 staff, active GSTIN
def test_scenario_04_small_multisite():
    profile = BusinessProfile(
        business_type="office",
        segment="multi",
        city_tier=1,
        employees=20,
        sites=3,
        gstin_active=True,
    )
    rec = app.state.eligibility.recommend(RecommendationRequest(profile=profile))
    assert any(d.product.product_id == "P03" for d in rec.eligible_products)


# 5. Small manufacturer, 1 site, 45 staff, active GSTIN
def test_scenario_05_small_manufacturer():
    profile = BusinessProfile(
        business_type="manufacturing",
        segment="mfg",
        city_tier=2,
        employees=45,
        sites=1,
        gstin_active=True,
    )
    rec = app.state.eligibility.recommend(RecommendationRequest(profile=profile))
    assert len(rec.eligible_products) > 0


# 6. Standalone product recommendation
def test_scenario_06_standalone_products():
    res = client.get("/api/catalog/products")
    assert res.status_code == 200
    products = res.json()["products"]
    standalone = [p for p in products if not p["requires_one_of"]]
    dependent = [p for p in products if p["requires_one_of"]]
    assert len(standalone) > 0
    assert len(dependent) > 0


# 7. Product requiring active GSTIN blocked when inactive
def test_scenario_07_gstin_block():
    profile = BusinessProfile(
        business_type="office",
        segment="prof",
        city_tier=1,
        employees=10,
        sites=1,
        gstin_active=False,
    )
    rec = app.state.eligibility.recommend(RecommendationRequest(profile=profile))
    ineligible_by_gstin = [
        d for d in rec.ineligible_products if "active GSTIN is required" in " ".join(d.reasons)
    ]
    assert len(ineligible_by_gstin) > 0


# 8. Minimum employee threshold blocked when below
def test_scenario_08_employee_threshold_block():
    profile = BusinessProfile(
        business_type="office",
        segment="prof",
        city_tier=1,
        employees=1,
        sites=1,
        gstin_active=True,
    )
    rec = app.state.eligibility.recommend(RecommendationRequest(profile=profile))
    emp_blocked = [
        d for d in rec.ineligible_products if "at least" in " ".join(d.reasons) and "employees" in " ".join(d.reasons)
    ]
    assert len(emp_blocked) > 0


# 9. Dependent product blocked without companion in bundle
def test_scenario_09_companion_product_validation():
    profile = BusinessProfile(
        business_type="office",
        segment="multi",
        city_tier=1,
        employees=20,
        sites=3,
        gstin_active=True,
    )
    # P10 requires one of P01, P02, P03
    request = RecommendationRequest(profile=profile)
    decisions = app.state.eligibility.validate_bundle(["P10"], request)
    assert not decisions[0].eligible
    assert "Requires one companion product" in decisions[0].reasons[0]


# 10. Quote pricing accuracy (setup fee flat for per-user, scaled for physical)
def test_scenario_10_pricing_accuracy():
    from app.schemas.products import Product
    from app.services.pricing import RateCard, calculate_line_item
    rate_card = RateCard()
    # P01: per site (physical) -> setup scales
    p01 = app.state.catalogue["P01"]
    line_p01 = calculate_line_item(p01, 3, rate_card)
    assert line_p01.setup_total == float(p01.one_time_setup_inr) * 3

    # P04: per user (software) -> setup is flat
    p04 = app.state.catalogue["P04"]
    line_p04 = calculate_line_item(p04, 10, rate_card)
    assert line_p04.setup_total == float(p04.one_time_setup_inr)


# 11. Quote generation and acceptance
def test_scenario_11_quote_generation_and_acceptance():
    profile = {
        "business_type": "office",
        "segment": "prof",
        "city_tier": 1,
        "employees": 10,
        "sites": 2,
        "gstin_active": True,
    }
    q = client.post("/api/quotes", json={
        "profile": profile,
        "items": [{"product_id": "P01", "quantity": 2}],
    }).json()
    assert q["status"] == "GENERATED"
    accepted = client.post(f"/api/quotes/{q['quote_id']}/accept").json()
    assert accepted["status"] == "ACCEPTED"
    assert accepted["accepted_at"] is not None


# 12. Feasibility simulation 4 states
def test_scenario_12_feasibility_states():
    res = client.post("/api/kyc/feasibility", json={"locations": [
        "Connaught Place, Delhi",
        "remote unserviceable hill",
        "new area survey required",
        "wireless 4g only sector",
    ]}).json()
    statuses = [s["status"] for s in res["sites"]]
    assert "AVAILABLE" in statuses
    assert "NOT_FEASIBLE" in statuses
    assert "SURVEY_REQUIRED" in statuses
    assert "ALTERNATIVE_AVAILABLE" in statuses


# 13. Consent gate enforcement
def test_scenario_13_consent_gate():
    aid = f"GATE-{uuid4()}"
    res = client.post("/api/kyc/documents", json={
        "applicant_id": aid,
        "document_type": "gst_certificate",
        "file_name": "K01_gst_certificate.png",
    })
    assert res.status_code == 403
    # Grant consent
    client.post("/api/kyc/consent", json={"applicant_id": aid, "granted": True})
    # Now accepted
    res2 = client.post("/api/kyc/documents", json={
        "applicant_id": aid,
        "document_type": "gst_certificate",
        "file_name": "K01_gst_certificate.png",
    })
    assert res2.status_code == 200


# 14. KYC document extraction and rule-based decision
def test_scenario_14_kyc_document_decision():
    aid = f"KYC-DEC-{uuid4()}"
    client.post("/api/kyc/consent", json={"applicant_id": aid, "granted": True})
    res = client.post("/api/kyc/documents", json={
        "applicant_id": aid,
        "document_type": "gst_certificate",
        "file_name": "K01_gst_certificate.png",
    }).json()
    assert res["status"] in ("VERIFIED", "ACTION_REQUIRED", "MANUAL_REVIEW")
    assert "reason" in res


# 15. Order state machine valid and invalid transitions
def test_scenario_15_order_transitions():
    profile = {
        "business_type": "clinic",
        "segment": "prof",
        "city_tier": 2,
        "employees": 12,
        "sites": 1,
        "gstin_active": True,
    }
    q = client.post("/api/quotes", json={
        "profile": profile,
        "items": [{"product_id": "P02", "quantity": 1}],
    }).json()
    client.post(f"/api/quotes/{q['quote_id']}/accept")
    order = client.post("/api/orders", json={
        "quote_id": q["quote_id"],
        "applicant_id": str(uuid4()),
        "location": "Mumbai",
    }).json()
    oid = order["order_id"]

    # Valid transition to KYC_PENDING
    t1 = client.post(f"/api/orders/{oid}/transition", json={
        "new_state": "KYC_PENDING", "reason": "Documents uploaded", "actor": "customer"
    })
    assert t1.status_code == 200

    # Invalid jump directly to ACTIVATED
    bad = client.post(f"/api/orders/{oid}/transition", json={
        "new_state": "ACTIVATED", "reason": "Shortcut", "actor": "customer"
    })
    assert bad.status_code == 409


# 16. Payment simulation success and retry after failure
def test_scenario_16_payment_simulation():
    profile = {
        "business_type": "clinic",
        "segment": "prof",
        "city_tier": 2,
        "employees": 12,
        "sites": 1,
        "gstin_active": True,
    }
    q = client.post("/api/quotes", json={
        "profile": profile,
        "items": [{"product_id": "P02", "quantity": 1}],
    }).json()
    client.post(f"/api/quotes/{q['quote_id']}/accept")
    order = client.post("/api/orders", json={
        "quote_id": q["quote_id"], "applicant_id": str(uuid4()), "location": "Delhi"
    }).json()
    oid = order["order_id"]

    for state in ("KYC_PENDING", "KYC_VERIFIED", "FEASIBILITY_CLEARED", "PAYMENT_PENDING"):
        client.post(f"/api/orders/{oid}/transition", json={"new_state": state, "reason": "step", "actor": "test"})

    # Fail
    f = client.post(f"/api/orders/{oid}/payment", json={"outcome": "FAILURE"}).json()
    assert f["status"] == "PAYMENT_FAILED"

    # Retry
    client.post(f"/api/orders/{oid}/transition", json={"new_state": "PAYMENT_PENDING", "reason": "retry", "actor": "test"})
    s = client.post(f"/api/orders/{oid}/payment", json={"outcome": "SUCCESS"}).json()
    assert s["status"] == "PAYMENT_CONFIRMED"


# 17. Installation slot scheduling with dynamic ETA
def test_scenario_17_installation_scheduling():
    profile = {
        "business_type": "clinic",
        "segment": "prof",
        "city_tier": 2,
        "employees": 12,
        "sites": 1,
        "gstin_active": True,
    }
    q = client.post("/api/quotes", json={
        "profile": profile,
        "items": [{"product_id": "P02", "quantity": 1}],
    }).json()
    client.post(f"/api/quotes/{q['quote_id']}/accept")
    order = client.post("/api/orders", json={
        "quote_id": q["quote_id"], "applicant_id": str(uuid4()), "location": "Mumbai"
    }).json()
    oid = order["order_id"]

    for state in ("KYC_PENDING", "KYC_VERIFIED", "FEASIBILITY_CLEARED", "PAYMENT_PENDING"):
        client.post(f"/api/orders/{oid}/transition", json={"new_state": state, "reason": "step", "actor": "test"})
    client.post(f"/api/orders/{oid}/payment", json={"outcome": "SUCCESS"})

    sched = client.post(f"/api/orders/{oid}/schedule", json={"location": "Mumbai"})
    assert sched.status_code == 200
    assert sched.json()["installation_status"] == "SCHEDULED"


# 18. Partner queue and live funnel analytics
def test_scenario_18_partner_queue_and_analytics():
    funnel = client.get("/api/analytics/funnel")
    assert funnel.status_code == 200
    fdata = funnel.json()
    assert "historical_baseline" in fdata
    assert "live_prototype" in fdata

    queue = client.get("/api/partner/queue")
    assert queue.status_code == 200
    qdata = queue.json()
    assert "items" in qdata
    assert "total" in qdata
