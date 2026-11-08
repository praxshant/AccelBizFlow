from typing import Any
from pydantic import BaseModel, Field

from app.schemas.eligibility import BusinessProfile, RecommendationResponse, QuoteResponse


class AdvisorMessageRequest(BaseModel):
    conversation_id: str | None = None
    message: str = Field(min_length=1, max_length=4000)


class AdvisorMessageResponse(BaseModel):
    conversation_id: str
    reply: str
    profile: BusinessProfile | dict[str, Any] | None = None
    missing_fields: list[str] = Field(default_factory=list)
    recommendations: RecommendationResponse | None = None
    quote: QuoteResponse | None = None


class ConversationResponse(BaseModel):
    conversation_id: str
    messages: list[dict[str, str]]
    profile: BusinessProfile | None = None
