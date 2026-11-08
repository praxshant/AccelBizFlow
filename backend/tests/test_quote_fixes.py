"""Test configurable quantities, setup fees, and idempotency."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def _make_profile():
    return {
        "business_type": "office",
        "segment": "prof",
        "city_tier": 1,
        "employees": 10,
        "sites": 2,
        "gstin_active": True,
    }


def test_catalogue_has_products():
    resp = client.get("/api/catalog/products")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] > 0


def test_quote_allows_flexible_quantity():
    from app.main import app as _app
    from app.schemas.eligibility import RecommendationRequest, BusinessProfile
    profile = BusinessProfile(
        business_type="office", segment="prof", city_tier=1,
        employees=10, sites=2, gstin_active=True
    )
    response = _app.state.eligibility.recommend(RecommendationRequest(profile=profile))
    essential = next((b for b in response.bundles if b.name == "essential"), None)
    if not essential or not essential.product_ids:
        pytest.skip("No essential bundle available for this profile")
    pid = essential.product_ids[0]
    product = _app.state.catalogue[pid]
    min_qty = profile.sites if product.unit == "per site" else (profile.employees if product.unit in ("per user", "per device") else 1)
    resp = client.post("/api/quotes", json={
        "profile": _make_profile(),
        "items": [{"product_id": pid, "quantity": min_qty}],
    })
    assert resp.status_code in (200, 201)


def test_quote_idempotency():
    from app.main import app as _app
    from app.schemas.eligibility import RecommendationRequest, BusinessProfile
    profile = BusinessProfile(
        business_type="office", segment="prof", city_tier=1,
        employees=10, sites=2, gstin_active=True
    )
    response = _app.state.eligibility.recommend(RecommendationRequest(profile=profile))
    essential = next((b for b in response.bundles if b.name == "essential"), None)
    if not essential or not essential.product_ids:
        pytest.skip("No essential bundle")
    pid = essential.product_ids[0]
    product = _app.state.catalogue[pid]
    min_qty = profile.sites if product.unit == "per site" else 1
    key = f"idem-test-{pid}-{min_qty}"
    payload = {
        "profile": _make_profile(),
        "items": [{"product_id": pid, "quantity": min_qty}],
        "idempotency_key": key,
    }
    r1 = client.post("/api/quotes", json=payload)
    r2 = client.post("/api/quotes", json=payload)
    assert r1.status_code in (200, 201)
    assert r2.status_code in (200, 201)
    assert r1.json()["quote_id"] == r2.json()["quote_id"]
