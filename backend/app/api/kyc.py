"""
KYC router – implements the full Roadmap Section 7 API surface.

Roadmap paths (now supported):
  POST /api/kyc/cases                        – create / open a KYC case
  POST /api/kyc/cases/{id}/consent           – record explicit consent for a case
  POST /api/kyc/cases/{id}/documents         – process a document for a case
  GET  /api/kyc/cases/{id}                   – retrieve KYC case status
  POST /api/kyc/cases/{id}/review            – reviewer decision (requires kyc_reviewer JWT)

Legacy paths retained for backwards compatibility with running test suite:
  POST /api/kyc/consent                      – shorthand consent (applicant_id in body)
  POST /api/kyc/documents                    – shorthand document upload (applicant_id in body)
  GET  /api/kyc/registry/{registry}/{id}     – direct registry lookup
  POST /api/kyc/feasibility                  – feasibility via KYC router
"""
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile

from app.auth import require_role
from app.schemas.kyc import (
    ConsentRequest, ConsentResponse, DocumentRequest, DocumentResult,
    FeasibilityRequest, FeasibilityResponse, KycCaseResponse, RegistryResponse,
    KycReviewRequest,
)

router = APIRouter(prefix="/kyc", tags=["feasibility", "kyc"])


# ---------------------------------------------------------------------------
# Roadmap-compliant paths
# ---------------------------------------------------------------------------

@router.post("/cases", response_model=KycCaseResponse, status_code=201)
def create_case(payload: ConsentRequest, request: Request):
    """Create or open a KYC case for an applicant."""
    return request.app.state.kyc.create_case(payload.applicant_id)


@router.post("/cases/{applicant_id}/consent", response_model=ConsentResponse)
def case_consent(applicant_id: str, payload: ConsentRequest, request: Request):
    return request.app.state.kyc.consent(applicant_id, payload.granted)


@router.post("/cases/{applicant_id}/documents", response_model=DocumentResult)
def case_document(applicant_id: str, payload: DocumentRequest, request: Request):
    try:
        return request.app.state.kyc.document(applicant_id, payload.document_type, payload.file_name)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/cases/{applicant_id}/documents/upload", response_model=DocumentResult)
async def case_document_upload(
    applicant_id: str,
    request: Request,
    document_type: str = Form(...),
    file: UploadFile = File(...),
):
    try:
        content = await file.read()
        return request.app.state.kyc.document_upload(applicant_id, document_type, file.filename, content)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/cases/{applicant_id}", response_model=KycCaseResponse)
def get_case(applicant_id: str, request: Request):
    try:
        return request.app.state.kyc.status(applicant_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="KYC case not found.") from exc


@router.post(
    "/cases/{applicant_id}/review",
    response_model=KycCaseResponse,
    dependencies=[Depends(require_role("kyc_reviewer", "kyc_admin"))],
)
def review_case(
    applicant_id: str,
    payload: KycReviewRequest,
    request: Request,
    reviewer: dict = Depends(require_role("kyc_reviewer", "kyc_admin")),
):
    """
    Review a KYC case. Reviewer identity and role are sourced exclusively from the
    validated JWT — the ``X-Reviewer-Id`` header is ignored.
    """
    try:
        return request.app.state.kyc.review(
            applicant_id,
            payload.status,
            payload.reason,
            reviewer_id=reviewer["identity"],
            reviewer_role=reviewer["role"],
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="KYC case not found.") from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Legacy / shorthand paths (backwards compat)
# ---------------------------------------------------------------------------

@router.post("/feasibility", response_model=FeasibilityResponse)
def feasibility(payload: FeasibilityRequest, request: Request):
    return request.app.state.kyc.feasibility(payload.locations)


@router.post("/consent", response_model=ConsentResponse)
def consent(payload: ConsentRequest, request: Request):
    return request.app.state.kyc.consent(payload.applicant_id, payload.granted)


@router.post("/consent/{applicant_id}/withdraw", response_model=ConsentResponse)
def withdraw_consent(applicant_id: str, request: Request):
    return request.app.state.kyc.consent(applicant_id, False)


@router.post("/documents", response_model=DocumentResult)
def process_document(payload: DocumentRequest, request: Request):
    try:
        return request.app.state.kyc.document(payload.applicant_id, payload.document_type, payload.file_name)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/registry/{registry}/{identifier}", response_model=RegistryResponse)
def verify_registry(registry: str, identifier: str, request: Request):
    normalized = registry.upper()
    if normalized not in {"GSTIN", "UDYAM"}:
        raise HTTPException(status_code=422, detail="Registry must be GSTIN or UDYAM.")
    return request.app.state.kyc.registry(normalized, identifier)
