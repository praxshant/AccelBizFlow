from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth import get_current_user
from app.schemas.orders import InstallationRequest, OrderCreateRequest, OrderResponse, OrderTransitionRequest, PaymentRequest

router = APIRouter(prefix="/orders", tags=["orders"])


def _service(request: Request):
    return request.app.state.orders


@router.post("", response_model=OrderResponse, status_code=201)
def create_order(payload: OrderCreateRequest, request: Request):
    try:
        return _service(request).create(payload.quote_id, payload.applicant_id, payload.location)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: str, request: Request):
    try:
        return _service(request).get(order_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Order not found.") from exc


@router.post(
    "/{order_id}/transition",
    response_model=OrderResponse,
)
def transition(
    order_id: str,
    payload: OrderTransitionRequest,
    request: Request,
):
    actor = payload.actor or "system"
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            from app.auth import decode_token, _secret
            payload_jwt = decode_token(auth_header[len("Bearer "):], _secret())
            actor = payload_jwt.get("sub", actor)
        except Exception:
            pass
    try:
        return _service(request).transition(
            order_id, payload.new_state, payload.reason, actor
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Order not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{order_id}/payment", response_model=OrderResponse)
def payment(order_id: str, payload: PaymentRequest, request: Request):
    try:
        return _service(request).payment(order_id, payload.outcome, payload.reason)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Order not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{order_id}/installation", response_model=OrderResponse)
@router.post("/{order_id}/schedule", response_model=OrderResponse)
def installation(order_id: str, payload: InstallationRequest, request: Request):
    try:
        return _service(request).schedule(order_id, payload.location)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Order not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
