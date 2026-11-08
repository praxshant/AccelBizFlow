"""
Prototype-only token issuance endpoint.

WARNING: This endpoint issues JWT tokens for ANY identity/role combination without
verifying credentials. It exists solely to exercise auth flows during development
and testing. In production, replace this with a real identity provider (e.g. OAuth2
/ OIDC). Do NOT expose this endpoint in a production deployment.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.auth import SUPPORTED_ROLES, create_access_token, _secret


router = APIRouter(prefix="/auth", tags=["auth"])


class TokenRequest(BaseModel):
    identity: str = Field(min_length=1, description="Unique subject identifier (e.g. user ID).")
    role: str = Field(
        min_length=1,
        description=f"Role to embed in the token. Must be one of: {sorted(SUPPORTED_ROLES)}.",
    )
    expiry_hours: int = Field(default=24, ge=1, le=168, description="Token lifetime in hours.")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    identity: str
    expires_in_hours: int


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="[PROTOTYPE ONLY] Issue a JWT for the given identity and role",
    description=(
        "**PROTOTYPE ONLY** — issues tokens without credential verification. "
        "Replace with a real identity provider before any production deployment."
    ),
)
def issue_token(payload: TokenRequest) -> TokenResponse:
    """Issue a signed JWT. This endpoint bypasses all credential checks and is for
    development/testing purposes ONLY."""
    if payload.role not in SUPPORTED_ROLES:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported role '{payload.role}'. Must be one of: {sorted(SUPPORTED_ROLES)}",
        )
    token = create_access_token(
        identity=payload.identity,
        role=payload.role,
        secret=_secret(),
        expiry_hours=payload.expiry_hours,
    )
    return TokenResponse(
        access_token=token,
        role=payload.role,
        identity=payload.identity,
        expires_in_hours=payload.expiry_hours,
    )
