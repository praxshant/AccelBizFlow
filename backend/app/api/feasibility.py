from fastapi import APIRouter, Request
from app.schemas.kyc import FeasibilityRequest, FeasibilityResponse

router = APIRouter(prefix="/feasibility", tags=["feasibility"])


@router.post("/check", response_model=FeasibilityResponse)
def check_feasibility(payload: FeasibilityRequest, request: Request):
    return request.app.state.kyc.feasibility(payload.locations)
