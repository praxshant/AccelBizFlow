from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_reports_catalogue_size():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "catalogue_products": 25}


def test_recommendation_endpoint_returns_decisions():
    response = client.post(
        "/api/recommendations/evaluate",
        json={
            "profile": {
                "business_type": "clinic",
                "segment": "professional offices",
                "city_tier": 2,
                "employees": 12,
                "sites": 1,
                "gstin_active": True,
            }
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["eligible_products"]) + len(body["ineligible_products"]) == 25
    eligible_ids = {item["product"]["product_id"] for item in body["eligible_products"]}
    assert {"P02", "P16", "P20"} <= eligible_ids


def test_recommendation_endpoint_rejects_unknown_selected_product():
    response = client.post(
        "/api/recommendations/evaluate",
        json={
            "profile": {
                "business_type": "clinic",
                "segment": "professional offices",
                "city_tier": 2,
                "employees": 12,
                "sites": 1,
                "gstin_active": True,
            },
            "selected_product_ids": ["P999"],
        },
    )

    assert response.status_code == 422
    assert "Unknown selected product IDs" in response.json()["detail"]
