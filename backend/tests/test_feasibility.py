"""Feasibility states and GSTIN registry tests."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_feasibility_available():
    resp = client.post("/api/kyc/feasibility", json={"locations": ["Mumbai"]})
    assert resp.status_code == 200
    data = resp.json()
    assert data["sites"][0]["status"] == "AVAILABLE"
    assert "checked_at" in data
    assert "valid_until_hours" in data


def test_feasibility_not_feasible():
    resp = client.post("/api/kyc/feasibility", json={"locations": ["remote site"]})
    assert resp.status_code == 200
    assert resp.json()["sites"][0]["status"] == "NOT_FEASIBLE"


def test_feasibility_survey_required():
    resp = client.post("/api/kyc/feasibility", json={"locations": ["new area survey needed"]})
    assert resp.status_code == 200
    assert resp.json()["sites"][0]["status"] == "SURVEY_REQUIRED"


def test_feasibility_alternative_available():
    resp = client.post("/api/kyc/feasibility", json={"locations": ["4g only zone"]})
    assert resp.status_code == 200
    assert resp.json()["sites"][0]["status"] == "ALTERNATIVE_AVAILABLE"


def test_feasibility_canonical_route():
    resp = client.post("/api/feasibility/check", json={"locations": ["Delhi"]})
    assert resp.status_code == 200
    assert resp.json()["sites"][0]["status"] == "AVAILABLE"


def test_registry_cancelled_gstin_returns_invalid():
    from pathlib import Path
    import csv
    data_root = Path(__file__).resolve().parents[2] / "YTL_TrackA_Udyam_Digital_Data"
    cancelled_id = None
    with (data_root / "mock_gstin_registry.csv").open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            status = row.get("status", row.get("Status", "")).strip()
            if status.lower() in ("cancelled", "suspended"):
                cancelled_id = list(row.values())[0].strip()
                break
    if not cancelled_id:
        pytest.skip("No cancelled GSTIN in registry")
    resp = client.get(f"/api/kyc/registry/GSTIN/{cancelled_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "INVALID"


def test_registry_active_gstin_returns_valid():
    from pathlib import Path
    import csv
    data_root = Path(__file__).resolve().parents[2] / "YTL_TrackA_Udyam_Digital_Data"
    active_id = None
    with (data_root / "mock_gstin_registry.csv").open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            status = row.get("status", row.get("Status", "")).strip()
            if status.lower() == "active":
                active_id = list(row.values())[0].strip()
                break
    if not active_id:
        pytest.skip("No active GSTIN in registry")
    resp = client.get(f"/api/kyc/registry/GSTIN/{active_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "VALID"
