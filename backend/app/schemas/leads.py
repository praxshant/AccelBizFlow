from pydantic import BaseModel, Field


class LeadCreateRequest(BaseModel):
    business_name: str = Field(min_length=1, max_length=200)
    contact_name: str = Field(min_length=1, max_length=200)
    phone: str = Field(min_length=7, max_length=40)
    city: str = Field(min_length=1, max_length=120)
    segment: str = Field(min_length=1, max_length=80)


class LeadResponse(LeadCreateRequest):
    lead_id: str
    created_at: str
