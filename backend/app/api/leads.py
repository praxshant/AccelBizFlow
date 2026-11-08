import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from app.database import ConversationRecord, LeadRecord

router = APIRouter(prefix="/leads", tags=["leads"])


class LeadCreateRequest(BaseModel):
    business_name: str = Field(min_length=1)
    contact_name: str = Field(min_length=1)
    contact_phone: str = Field(min_length=1)
    segment: str = Field(min_length=1)
    city: str = Field(min_length=1)
    source: str = "api"


def _lead_response(lead, status="NEW"):
    return {
        "lead_id": lead.lead_id,
        "business_name": lead.business_name,
        "contact_name": lead.contact_name,
        "contact_phone": lead.phone,
        "segment": lead.segment,
        "city": lead.city,
        "status": status,
        "created_at": lead.created_at.isoformat(),
        "archived_at": lead.archived_at.isoformat() if lead.archived_at else None,
    }


def _lead_status(session, lead_id):
    if session.query(ConversationRecord).filter_by(lead_id=lead_id).first():
        return "DISCOVERY"
    return "NEW"


@router.post("", status_code=201)
def create_lead(payload: LeadCreateRequest, request: Request):
    lead_id = f"L-{str(uuid.uuid4())[:8].upper()}"
    with request.app.state.db_session.begin() as session:
        lead = LeadRecord(
            lead_id=lead_id,
            business_name=payload.business_name,
            contact_name=payload.contact_name,
            phone=payload.contact_phone,
            city=payload.city,
            segment=payload.segment,
        )
        session.add(lead)
        session.flush()
        response = _lead_response(lead)
        response["source"] = payload.source
        return response


@router.get("")
def list_leads(request: Request, include_archived: bool = False):
    with request.app.state.db_session() as session:
        query = session.query(LeadRecord).order_by(LeadRecord.created_at.desc())
        if not include_archived:
            query = query.filter(LeadRecord.archived_at.is_(None))
        return [_lead_response(lead, _lead_status(session, lead.lead_id)) for lead in query.all()]


@router.get("/{lead_id}")
def get_lead(lead_id: str, request: Request):
    with request.app.state.db_session() as session:
        lead = session.get(LeadRecord, lead_id)
        if lead is None:
            raise HTTPException(status_code=404, detail=f"Lead {lead_id} not found.")
        return _lead_response(lead, _lead_status(session, lead.lead_id))


@router.post("/{lead_id}/archive")
def archive_lead(lead_id: str, request: Request):
    with request.app.state.db_session.begin() as session:
        lead = session.get(LeadRecord, lead_id)
        if lead is None:
            raise HTTPException(status_code=404, detail=f"Lead {lead_id} not found.")
        lead.archived_at = datetime.now(timezone.utc)
        return _lead_response(lead, "ARCHIVED")


@router.delete("/{lead_id}")
def delete_lead(lead_id: str, request: Request):
    with request.app.state.db_session.begin() as session:
        lead = session.get(LeadRecord, lead_id)
        if lead is None:
            raise HTTPException(status_code=404, detail=f"Lead {lead_id} not found.")
        if session.query(ConversationRecord).filter_by(lead_id=lead_id).first():
            raise HTTPException(
                status_code=409,
                detail="This lead has linked business records. Archive it instead.",
            )
        session.delete(lead)
        return {"deleted": True, "lead_id": lead_id}
