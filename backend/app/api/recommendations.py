from fastapi import APIRouter, Depends, HTTPException, Request

from app.schemas.eligibility import RecommendationRequest, RecommendationResponse
from app.services.eligibility.engine import EligibilityEngine
from app.schemas.products import Product


router = APIRouter(tags=["recommendations"])


def get_catalogue(request: Request) -> dict[str, Product]:
    return request.app.state.catalogue


@router.post("/recommendations/evaluate", response_model=RecommendationResponse)
def evaluate_recommendations(
    request: RecommendationRequest,
    catalogue: dict[str, Product] = Depends(get_catalogue),
) -> RecommendationResponse:
    engine = EligibilityEngine(catalogue)
    try:
        return engine.recommend(request)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
