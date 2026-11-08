from pydantic import BaseModel, Field


class LeadScoreResponse(BaseModel):
    lead_id: str
    score: int
    reasons: list[str]


class AssignmentRequest(BaseModel):
    case_type: str = Field(min_length=1, max_length=40)
    case_id: str = Field(min_length=1, max_length=100)
    owner: str = Field(min_length=1, max_length=100)


class AssignmentResponse(BaseModel):
    assignment_id: int
    case_type: str
    case_id: str
    owner: str
    status: str


class QueueItem(BaseModel):
    case_type: str
    case_id: str
    status: str
    priority: str


class QueueResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[QueueItem]
