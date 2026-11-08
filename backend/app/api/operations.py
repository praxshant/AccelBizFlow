from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.auth import require_role
from app.database import HumanAssistanceRecord
from app.schemas.operations import AssignmentRequest, AssignmentResponse, LeadScoreResponse, QueueResponse
from pydantic import BaseModel, Field
import uuid

router = APIRouter(tags=["operations", "analytics"])


class AssistanceRequest(BaseModel):
    stage: str = Field(min_length=1, max_length=50)
    reason: str = Field(min_length=1, max_length=500)
    applicant_id: str | None = None
    lead_id: str | None = None


@router.post("/assistance", status_code=201)
def request_assistance(payload: AssistanceRequest, request: Request):
    with request.app.state.db_session.begin() as session:
        case = HumanAssistanceRecord(
            case_id=str(uuid.uuid4()),
            applicant_id=payload.applicant_id,
            lead_id=payload.lead_id,
            stage=payload.stage,
            reason=payload.reason,
        )
        session.add(case)
        session.flush()
        return {
            "case_id": case.case_id,
            "stage": case.stage,
            "reason": case.reason,
            "status": case.status,
            "applicant_id": case.applicant_id,
            "lead_id": case.lead_id,
        }


@router.get("/analytics/funnel")
def funnel(request: Request):
    return request.app.state.analytics.funnel()


@router.get("/analytics/segments")
def segments(request: Request):
    return request.app.state.analytics.segments()


@router.get("/analytics/leads/{lead_id}/score", response_model=LeadScoreResponse)
def score(lead_id: str, request: Request):
    try:
        return request.app.state.analytics.score(lead_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Lead not found.") from exc


@router.get("/partner/queue", response_model=QueueResponse)
def queue(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    case_type: str | None = Query(None),
    priority: str | None = Query(None),
):
    return request.app.state.analytics.queue(page, page_size, case_type, priority)


@router.get("/sales/queue")
def sales_queue(request: Request, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    return request.app.state.analytics.sales_queue(page, page_size)


@router.post(
    "/partner/assignments",
    response_model=AssignmentResponse,
    status_code=201,
    dependencies=[Depends(require_role("partner", "admin"))],
)
def assign(payload: AssignmentRequest, request: Request):
    """Create a partner assignment. Requires ``partner`` or ``admin`` role."""
    return request.app.state.analytics.assign(payload.case_type, payload.case_id, payload.owner)
