from typing import Literal
from pydantic import BaseModel, Field


OrderStatus = Literal[
    "DRAFT", "QUOTE_ACCEPTED", "KYC_PENDING", "KYC_VERIFIED",
    "FEASIBILITY_CLEARED", "PAYMENT_PENDING", "PAYMENT_CONFIRMED",
    "INSTALLATION_SCHEDULED", "INSTALLATION_IN_PROGRESS",
    "SERVICE_INSTALLED", "ACTIVATED", "KYC_ACTION_REQUIRED",
    "KYC_MANUAL_REVIEW", "KYC_REJECTED", "FEASIBILITY_SURVEY_REQUIRED",
    "FEASIBILITY_UNAVAILABLE", "PAYMENT_FAILED", "INSTALLATION_BLOCKED",
    "CANCELLED",
]


class OrderCreateRequest(BaseModel):
    quote_id: str = Field(min_length=1)
    applicant_id: str = Field(min_length=1)
    location: str = Field(min_length=1, max_length=300)


class OrderTransitionRequest(BaseModel):
    new_state: OrderStatus
    reason: str = Field(min_length=1, max_length=500)
    actor: str = Field(min_length=1, max_length=100)


class PaymentRequest(BaseModel):
    outcome: Literal["SUCCESS", "FAILURE"]
    reason: str | None = Field(default=None, max_length=500)


class InstallationRequest(BaseModel):
    location: str = Field(min_length=1, max_length=300)


class OrderResponse(BaseModel):
    order_id: str
    quote_id: str
    status: OrderStatus
    payment_status: str
    installation_status: str
    snapshot: dict
    events: list[dict]


class AssignmentRequest(BaseModel):
    case_type: str = Field(min_length=1, max_length=40)
    case_id: str = Field(min_length=1, max_length=100)
    owner: str = Field(min_length=1, max_length=100)
