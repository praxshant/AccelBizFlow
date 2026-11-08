"""
JWT-based authentication module for Accel BizFlow.

Uses python-jose (available in the runtime environment) to sign/verify HS256 tokens.

Environment variable:
  JWT_SECRET  — shared secret for HMAC-SHA256 signing.
                Default: "dev-secret-change-in-production"
                MUST be overridden via .env in any non-development deployment.

Supported roles:
  customer | sales | kyc_reviewer | kyc_admin | partner | admin
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request
from jose import ExpiredSignatureError, JWTError, jwt


SUPPORTED_ROLES: frozenset[str] = frozenset(
    {"customer", "sales", "kyc_reviewer", "kyc_admin", "partner", "admin"}
)

ALGORITHM = "HS256"


class AuthError(Exception):
    """Raised when a token is invalid, expired, or structurally malformed."""


def _secret() -> str:
    """Read JWT_SECRET from the environment at call-time (never cached at module level)."""
    return os.getenv("JWT_SECRET", "dev-secret-change-in-production")


def create_access_token(
    identity: str,
    role: str,
    secret: str,
    expiry_hours: int = 24,
) -> str:
    """
    Issue a signed JWT for the given identity and role.

    Args:
        identity:     Unique identifier for the subject (e.g. user ID, e-mail).
        role:         One of SUPPORTED_ROLES.
        secret:       HMAC signing secret.
        expiry_hours: Token lifetime in hours (default 24 h).

    Returns:
        A compact JWT string.

    Raises:
        ValueError: If role is not in SUPPORTED_ROLES.
    """
    if role not in SUPPORTED_ROLES:
        raise ValueError(f"Unsupported role '{role}'. Must be one of {sorted(SUPPORTED_ROLES)}.")
    now = datetime.now(timezone.utc)
    payload = {
        "sub": identity,
        "role": role,
        "iat": now,
        "exp": now + timedelta(hours=expiry_hours),
    }
    return jwt.encode(payload, secret, algorithm=ALGORITHM)


def decode_token(token: str, secret: str) -> dict:
    """
    Decode and verify a JWT, returning the payload dict.

    Args:
        token:  Compact JWT string.
        secret: HMAC signing secret.

    Returns:
        Decoded payload (dict) containing at least ``sub`` and ``role``.

    Raises:
        AuthError: If the token is expired, has an invalid signature, or is malformed.
    """
    try:
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
    except ExpiredSignatureError as exc:
        raise AuthError("Token has expired.") from exc
    except JWTError as exc:
        raise AuthError(f"Invalid token: {exc}") from exc
    return payload


def get_current_user(request: Request) -> dict:
    """
    FastAPI dependency — extracts and validates the Bearer token from the
    ``Authorization`` header.

    Returns:
        ``{"identity": str, "role": str}``

    Raises:
        HTTP 401: If the header is missing, malformed, or the token is invalid/expired.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header.")
    token = auth_header[len("Bearer "):]
    try:
        payload = decode_token(token, _secret())
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    identity = payload.get("sub")
    role = payload.get("role")
    if not identity or not role:
        raise HTTPException(status_code=401, detail="Token payload is incomplete.")
    return {"identity": identity, "role": role}


def require_role(*roles: str):
    """
    FastAPI dependency factory — returns a dependency that checks the authenticated
    user has one of the specified roles.

    Usage:
        @router.post("/...", dependencies=[Depends(require_role("kyc_reviewer", "kyc_admin"))])

    Returns:
        A callable FastAPI dependency.

    Raises:
        HTTP 401: If the token is missing/invalid.
        HTTP 403: If the authenticated user's role is not in the allowed set.
    """
    allowed = frozenset(roles)

    def _dependency(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in allowed:
            raise HTTPException(
                status_code=403,
                detail=f"Role '{user['role']}' is not permitted. Required: {sorted(allowed)}.",
            )
        return user

    return _dependency
