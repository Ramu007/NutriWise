"""Cognito JWT verification.

Validates access tokens against the pool's JWKS. JWKS is fetched lazily on
first use and cached in-process; on unknown `kid` we refetch once (covers
Cognito's key rotation without needing a scheduled job).

Dev bypass: when running with `ENV=dev` and no `cognito_user_pool_id`
configured, we trust `X-User-Id`/`X-User-Role` headers so local development
and tests don't need real tokens. Production sets the pool id and all
protected routes require `Authorization: Bearer <access_token>`.

We verify the **access token** (not the ID token). Access tokens carry
`sub`, `cognito:groups`, and `client_id` — enough to identify the caller
and authorize by role. Email is on the ID token; we leave `Principal.email`
as `None` for now and can add `/oauth2/userInfo` later if the mobile app
needs it server-side.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx
from fastapi import Depends, HTTPException, Request, status
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JOSEError, JWTError

from .config import Settings, get_settings

_ALG = "RS256"
_ROLE_BY_GROUP = {
    "admins": "admin",
    "nutritionists": "nutritionist",
    "customers": "customer",
}


@dataclass(frozen=True)
class Principal:
    user_id: str
    email: str | None = None
    role: str = "customer"  # customer | nutritionist | admin


class _JWKSCache:
    """Per-process JWKS cache keyed by `kid`. Refetches on cache miss."""

    def __init__(self) -> None:
        self._keys: dict[str, dict[str, Any]] = {}
        self._url: str | None = None

    def configure(self, jwks_url: str) -> None:
        if jwks_url != self._url:
            # Pool changed (usually test->prod or env swap) — drop stale keys.
            self._keys.clear()
            self._url = jwks_url

    def get(self, kid: str) -> dict[str, Any] | None:
        return self._keys.get(kid)

    def refresh(self) -> None:
        assert self._url is not None
        data = httpx.get(self._url, timeout=5.0).json()
        self._keys = {k["kid"]: k for k in data.get("keys", [])}


_jwks = _JWKSCache()


def _jwks_url(region: str, pool_id: str) -> str:
    return f"https://cognito-idp.{region}.amazonaws.com/{pool_id}/.well-known/jwks.json"


def _issuer(region: str, pool_id: str) -> str:
    return f"https://cognito-idp.{region}.amazonaws.com/{pool_id}"


def _resolve_key(kid: str) -> dict[str, Any]:
    key = _jwks.get(kid)
    if key is None:
        # Unknown kid usually means rotation — try once more after refetch.
        _jwks.refresh()
        key = _jwks.get(kid)
    if key is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "unknown signing key")
    return key


def _principal_from_claims(claims: dict[str, Any]) -> Principal:
    sub = claims.get("sub")
    if not sub:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "token missing sub")
    groups: list[str] = claims.get("cognito:groups") or []
    role = "customer"
    # Admin wins over nutritionist wins over customer if user is in several groups.
    for g in ("admins", "nutritionists", "customers"):
        if g in groups:
            role = _ROLE_BY_GROUP[g]
            break
    return Principal(user_id=sub, email=None, role=role)


def _verify_access_token(token: str, settings: Settings) -> Principal:
    assert settings.cognito_user_pool_id is not None
    _jwks.configure(_jwks_url(settings.aws_region, settings.cognito_user_pool_id))
    try:
        unverified = jwt.get_unverified_header(token)
    except JWTError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "malformed token") from e
    kid = unverified.get("kid")
    if not kid:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "token missing kid")
    key = _resolve_key(kid)

    try:
        # Access tokens don't carry `aud`; skip that check and match client_id below.
        claims = jwt.decode(
            token,
            key,
            algorithms=[_ALG],
            issuer=_issuer(settings.aws_region, settings.cognito_user_pool_id),
            options={"verify_aud": False},
        )
    except ExpiredSignatureError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "token expired") from e
    except JOSEError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"invalid token: {e}") from e

    if claims.get("token_use") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "expected access token")
    if (
        settings.cognito_app_client_id
        and claims.get("client_id") != settings.cognito_app_client_id
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "token client_id mismatch")

    return _principal_from_claims(claims)


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
    token = auth.split(" ", 1)[1].strip()
    return _verify_access_token(token, settings)


def require_role(*allowed: str):
    def _dep(p: Principal = Depends(get_current_principal)) -> Principal:
        if p.role not in allowed:
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"role {p.role!r} not allowed")
        return p

    return _dep


# Test-only helper: lets tests inject a JWKS without hitting the network.
def _install_test_jwks(jwks_url: str, keys: list[dict[str, Any]]) -> None:
    _jwks.configure(jwks_url)
    _jwks._keys = {k["kid"]: k for k in keys}  # noqa: SLF001


def _reset_jwks_cache() -> None:
    _jwks._keys.clear()  # noqa: SLF001
    _jwks._url = None  # noqa: SLF001
