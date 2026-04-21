"""Cognito JWT validation.

Phase 0 stub — validates token signature against Cognito JWKS if credentials are set,
otherwise returns a dev principal. Real JWKS caching + kid rotation lands in Phase 1.
"""
from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, status

from .config import Settings, get_settings


@dataclass(frozen=True)
class Principal:
    user_id: str
    email: str | None = None
    role: str = "customer"  # customer | nutritionist | admin


def _dev_principal(request: Request) -> Principal:
    # Dev bypass: trust an X-User-Id header for local testing.
    uid = request.headers.get("x-user-id", "dev-user")
    email = request.headers.get("x-user-email")
    role = request.headers.get("x-user-role", "customer")
    return Principal(user_id=uid, email=email, role=role)


def get_current_principal(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> Principal:
    if settings.env == "dev" and not settings.cognito_user_pool_id:
        return _dev_principal(request)

    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing bearer token")

    # TODO(phase-1): fetch Cognito JWKS, verify signature + claims, extract sub/email/custom:role
    # For now, treat the token as opaque and stub a principal.
    return Principal(user_id="cognito-stub", email=None, role="customer")


def require_role(*allowed: str):
    def _dep(p: Principal = Depends(get_current_principal)) -> Principal:
        if p.role not in allowed:
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"role {p.role!r} not allowed")
        return p

    return _dep
