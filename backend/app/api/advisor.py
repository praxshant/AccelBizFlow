import uuid
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.database import ConversationRecord
from app.schemas.advisor import AdvisorMessageRequest, AdvisorMessageResponse, ConversationResponse

router = APIRouter(prefix="/advisor", tags=["advisor"])


class SessionCreateResponse(BaseModel):
    session_id: str
    messages: list[dict[str, str]] = []


class SessionCreateRequest(BaseModel):
    lead_id: str | None = None


class SessionMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


@router.post("/sessions", response_model=SessionCreateResponse, status_code=201)
def create_session(request: Request, payload: SessionCreateRequest = SessionCreateRequest()):
    cid = str(uuid.uuid4())
    with request.app.state.db_session.begin() as session:
        session.add(ConversationRecord(conversation_id=cid, lead_id=payload.lead_id, profile_json="{}"))
    return {"session_id": cid, "messages": []}


@router.get("/sessions")
def list_sessions(request: Request, lead_id: str):
    with request.app.state.db_session() as session:
        records = session.query(ConversationRecord).filter_by(lead_id=lead_id).order_by(
            ConversationRecord.updated_at.desc()
        ).all()
        return [{"session_id": record.conversation_id, "updated_at": record.updated_at.isoformat()} for record in records]


@router.post("/sessions/{session_id}/messages", response_model=AdvisorMessageResponse)
def session_message(session_id: str, payload: SessionMessageRequest, request: Request):
    return request.app.state.conversations_service.message(session_id, payload.message)


@router.get("/sessions/{session_id}", response_model=ConversationResponse)
def get_session(session_id: str, request: Request):
    try:
        return request.app.state.conversations_service.get(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Session not found.") from exc


@router.post("/message", response_model=AdvisorMessageResponse)
def send_message(payload: AdvisorMessageRequest, request: Request):
    return request.app.state.conversations_service.message(payload.conversation_id, payload.message)


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation(conversation_id: str, request: Request):
    try:
        return request.app.state.conversations_service.get(conversation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Conversation not found.") from exc
