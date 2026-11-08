"""KYC document processing pipeline tests."""
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
DATA_ROOT = Path(__file__).resolve().parents[2] / "YTL_TrackA_Udyam_Digital_Data"
DOC_ROOT = DATA_ROOT / "kyc_documents"


@pytest.fixture(scope="module")
def applicant():
    aid = "TEST-OCR-01"
    client.post("/api/kyc/consent", json={"applicant_id": aid, "granted": True})
    return aid


def test_consent_workflow(applicant):
    resp = client.post("/api/kyc/consent", json={"applicant_id": applicant, "granted": True})
    assert resp.status_code == 200
    data = resp.json()
    assert data["granted"] is True
    assert data["consented_at"] is not None


def test_document_requires_consent():
    resp = client.post("/api/kyc/documents", json={
        "applicant_id": "NO-CONSENT-99",
        "document_type": "gst_certificate",
        "file_name": "K01_gst_certificate.png",
    })
    assert resp.status_code == 403


def test_document_processing_returns_valid_status(applicant):
    docs = list(DOC_ROOT.glob("K01_*.png"))
    if not docs:
        pytest.skip("No K01 documents found")
    doc = docs[0]
    doc_type = doc.stem.split("_", 1)[1]
    resp = client.post("/api/kyc/documents", json={
        "applicant_id": applicant,
        "document_type": doc_type,
        "file_name": doc.name,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in {"VERIFIED", "ACTION_REQUIRED", "MANUAL_REVIEW"}
    assert "field_confidence" in data
    assert "reason" in data


def test_kyc_case_status_retrievable(applicant):
    resp = client.get(f"/api/kyc/cases/{applicant}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["applicant_id"] == applicant
    assert data["status"] in {"VERIFIED", "ACTION_REQUIRED", "MANUAL_REVIEW", "REJECTED"}
