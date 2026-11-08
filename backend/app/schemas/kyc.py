from typing import Literal
from typing import Any
from pydantic import BaseModel, Field


KycStatus = Literal["VERIFIED", "ACTION_REQUIRED", "MANUAL_REVIEW", "REJECTED"]


class FeasibilityRequest(BaseModel):
    locations: list[str] = Field(min_length=1)
    applicant_id: str | None = None


class FeasibilitySite(BaseModel):
    location: str
    status: Literal["AVAILABLE", "ALTERNATIVE_AVAILABLE", "SURVEY_REQUIRED", "NOT_FEASIBLE"]
    reason: str
    scheduling_available: bool


class FeasibilityResponse(BaseModel):
    sites: list[FeasibilitySite]
    checked_at: str
    valid_until_hours: int


class ConsentRequest(BaseModel):
    applicant_id: str = Field(min_length=1)
    granted: bool


class ConsentResponse(BaseModel):
    applicant_id: str
    granted: bool
    consented_at: str | None = None


class DocumentRequest(BaseModel):
    applicant_id: str | None = None
    document_type: Literal["gst_certificate", "udyam_certificate", "address_proof", "signatory_id"]
    file_name: str = Field(min_length=1)


class DocumentResult(BaseModel):
    applicant_id: str
    document_type: str
    status: KycStatus
    fields: dict[str, str] = Field(default_factory=dict)
    field_confidence: dict[str, float] = Field(default_factory=dict)
    reason: str


class RegistryResponse(BaseModel):
    registry: Literal["GSTIN", "UDYAM"]
    identifier_masked: str
    status: Literal["VALID", "INVALID", "MANUAL_REVIEW"]
    reason: str


class KycCaseResponse(BaseModel):
    applicant_id: str
    status: KycStatus
    reasons: list[str]
    audit: list[dict[str, Any]]


class KycReviewRequest(BaseModel):
    status: KycStatus
    reason: str = Field(min_length=1, max_length=500)
    reviewer_role: Literal["kyc_reviewer", "kyc_admin"]
