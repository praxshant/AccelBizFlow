from uuid import uuid4
from pathlib import Path

from app.main import app
from fastapi.testclient import TestClient


client = TestClient(app)


def lead_payload(name: str):
    return {
        "business_name": name,
        "contact_name": "Demo User",
        "contact_phone": "9999999999",
        "city": "Jaipur",
        "segment": "Professional offices",
    }


def test_leads_can_be_listed_and_switched_without_mixing_sessions():
    first = client.post("/api/leads", json=lead_payload(f"Lead A {uuid4()}"))
    second = client.post("/api/leads", json=lead_payload(f"Lead B {uuid4()}"))
    first_id = first.json()["lead_id"]
    second_id = second.json()["lead_id"]

    first_session = client.post("/api/advisor/sessions", json={"lead_id": first_id}).json()["session_id"]
    second_session = client.post("/api/advisor/sessions", json={"lead_id": second_id}).json()["session_id"]

    assert first_session != second_session
    assert client.get("/api/advisor/sessions", params={"lead_id": first_id}).json()[0]["session_id"] == first_session
    assert client.get("/api/advisor/sessions", params={"lead_id": second_id}).json()[0]["session_id"] == second_session


def test_linked_leads_are_archived_and_not_permanently_deleted():
    response = client.post("/api/leads", json=lead_payload(f"Linked Lead {uuid4()}"))
    lead_id = response.json()["lead_id"]
    client.post("/api/advisor/sessions", json={"lead_id": lead_id})

    assert client.post(f"/api/leads/{lead_id}/archive").status_code == 200
    assert all(item["lead_id"] != lead_id for item in client.get("/api/leads").json())
    assert client.delete(f"/api/leads/{lead_id}").status_code == 409


def test_unlinked_leads_can_be_permanently_deleted():
    response = client.post("/api/leads", json=lead_payload(f"Draft Lead {uuid4()}"))
    lead_id = response.json()["lead_id"]

    assert client.delete(f"/api/leads/{lead_id}").json() == {"deleted": True, "lead_id": lead_id}
    assert client.get(f"/api/leads/{lead_id}").status_code == 404


def test_advisor_uses_follow_up_context_for_short_answers():
    response = client.post("/api/advisor/message", json={"message": "meri bakery Jaipur mein hai"})
    assert response.status_code == 200
    conversation_id = response.json()["conversation_id"]
    assert response.json()["missing_fields"][0] == "employees"

    answer = client.post(
        "/api/advisor/message",
        json={"conversation_id": conversation_id, "message": "5"},
    )
    assert answer.status_code == 200
    assert answer.json()["profile"]["employees"] == 5


def test_operator_queues_are_filtered_by_work_type():
    sales = client.get("/api/sales/queue")
    reviewer = client.get("/api/partner/queue", params={"case_type": "kyc"})
    assert sales.status_code == 200
    assert all(item["case_type"] == "lead" for item in sales.json()["items"])
    assert reviewer.status_code == 200
    assert all(item["case_type"] == "kyc" for item in reviewer.json()["items"])


def test_assistance_is_persisted_and_multipart_kyc_is_processed():
    assistance = client.post(
        "/api/assistance",
        json={"stage": "feasibility", "reason": "Coverage review requested"},
    )
    assert assistance.status_code == 201
    case_id = assistance.json()["case_id"]
    queue = client.get("/api/partner/queue", params={"case_type": "assistance"})
    assert any(item["case_id"] == case_id for item in queue.json()["items"])

    applicant = f"UPLOAD-KYC-{uuid4()}"
    client.post("/api/kyc/cases", json={"applicant_id": applicant, "granted": False})
    client.post(
        f"/api/kyc/cases/{applicant}/consent",
        json={"applicant_id": applicant, "granted": True},
    )
    specimen = (
        Path(__file__).parents[2]
        / "YTL_TrackA_Udyam_Digital_Data"
        / "kyc_documents"
        / "K07_gst_certificate.png"
    )
    response = client.post(
        f"/api/kyc/cases/{applicant}/documents/upload",
        data={"document_type": "gst_certificate"},
        files={"file": ("K07_gst_certificate.png", specimen.read_bytes(), "image/png")},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "VERIFIED"
