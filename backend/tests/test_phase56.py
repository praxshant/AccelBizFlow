from uuid import uuid4

from fastapi.testclient import TestClient

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


def _accepted_quote():
    quote = client.post(
        "/api/quotes",
        json={"profile": PROFILE, "items": [{"product_id": "P02", "quantity": 1}]},
    ).json()
    client.post(f"/api/quotes/{quote['quote_id']}/accept")
    return quote["quote_id"]


def _order():
    response = client.post(
        "/api/orders",
        json={
            "quote_id": _accepted_quote(),
            "applicant_id": str(uuid4()),
            "location": "Delhi",
        },
    )
    assert response.status_code == 201
    return response.json()["order_id"]


def test_order_requires_accepted_quote_and_duplicate_is_idempotent():
    quote = client.post(
        "/api/quotes",
        json={"profile": PROFILE, "items": [{"product_id": "P02", "quantity": 1}]},
    ).json()
    rejected = client.post(
        "/api/orders",
        json={"quote_id": quote["quote_id"], "applicant_id": str(uuid4()), "location": "Delhi"},
    )
    assert rejected.status_code == 409
    accepted_quote = _accepted_quote()
    payload = {"quote_id": accepted_quote, "applicant_id": str(uuid4()), "location": "Delhi"}
    first = client.post("/api/orders", json=payload)
    second = client.post("/api/orders", json=payload)
    assert first.json()["order_id"] == second.json()["order_id"]


def test_payment_failure_can_retry_but_does_not_activate():
    order_id = _order()
    for state in ("KYC_PENDING", "KYC_VERIFIED", "FEASIBILITY_CLEARED", "PAYMENT_PENDING"):
        assert client.post(
            f"/api/orders/{order_id}/transition",
            json={"new_state": state, "reason": "test", "actor": "test"},
        ).status_code == 200
    failed = client.post(f"/api/orders/{order_id}/payment", json={"outcome": "FAILURE"})
    assert failed.json()["status"] == "PAYMENT_FAILED"
    assert client.post(
        f"/api/orders/{order_id}/transition",
        json={"new_state": "PAYMENT_PENDING", "reason": "retry", "actor": "test"},
    ).status_code == 200
    success = client.post(f"/api/orders/{order_id}/payment", json={"outcome": "SUCCESS"})
    assert success.json()["status"] == "PAYMENT_CONFIRMED"


def test_non_feasible_site_cannot_be_scheduled():
    order_id = _order()
    for state in ("KYC_PENDING", "KYC_VERIFIED", "FEASIBILITY_CLEARED", "PAYMENT_PENDING"):
        client.post(
            f"/api/orders/{order_id}/transition",
            json={"new_state": state, "reason": "test", "actor": "test"},
        )
    client.post(f"/api/orders/{order_id}/payment", json={"outcome": "SUCCESS"})
    response = client.post(
        f"/api/orders/{order_id}/installation",
        json={"location": "remote unserviceable site"},
    )
    assert response.status_code == 409


def test_partner_queue_pagination_and_score_are_deterministic():
    first = client.get("/api/analytics/leads/L00001/score").json()
    second = client.get("/api/analytics/leads/L00001/score").json()
    assert first == second
    queue = client.get("/api/partner/queue?page=1&page_size=2")
    assert queue.status_code == 200
    assert len(queue.json()["items"]) <= 2
