from fastapi import APIRouter, HTTPException, Request

from app.schemas.eligibility import QuoteCreateRequest, QuoteItemsPatchRequest, QuoteResponse
from app.services.quotes import QuoteService

router = APIRouter(prefix="/quotes", tags=["quotes"])


def service(request: Request):
    return request.app.state.db_session()


@router.post("", response_model=QuoteResponse, status_code=201)
def create_quote(payload: QuoteCreateRequest, request: Request):
    try:
        with service(request) as session:
            return QuoteService(session, request.app.state.catalogue, request.app.state.eligibility).create(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{quote_id}", response_model=QuoteResponse)
def get_quote(quote_id: str, request: Request):
    try:
        with service(request) as session:
            return QuoteService(session, request.app.state.catalogue, request.app.state.eligibility).get(quote_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Quote not found.") from exc


@router.patch("/{quote_id}/items", response_model=QuoteResponse)
def modify_quote(quote_id: str, payload: QuoteItemsPatchRequest, request: Request):
    try:
        with service(request) as session:
            return QuoteService(session, request.app.state.catalogue, request.app.state.eligibility).update_items(quote_id, payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Quote not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{quote_id}/accept", response_model=QuoteResponse)
def accept_quote(quote_id: str, request: Request):
    try:
        with service(request) as session:
            return QuoteService(session, request.app.state.catalogue, request.app.state.eligibility).accept(quote_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Quote not found.") from exc
