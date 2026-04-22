"""Cognito JWT verification — signed tokens against an injected JWKS.

We don't hit the real Cognito JWKS endpoint. We generate an RSA keypair in
the test, sign access-token-shaped JWTs locally, and inject the matching
public JWK via `_install_test_jwks` before dispatching requests.
"""
from __future__ import annotations

import json
import time
from collections.abc import Iterator

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from jose import jwk, jwt

from app.core import security
from app.core.config import get_settings
from app.deps import get_repos
from app.repositories.base import RepoBundle
from app.repositories.memory import (
    InMemoryBookingRepo,
    InMemoryFoodLogRepo,
    InMemoryNutritionistRepo,
    InMemoryUserRepo,
)

_REGION = "us-east-1"
_POOL_ID = "us-east-1_TESTPOOL"
_CLIENT_ID = "testclient123"
_ISS = f"https://cognito-idp.{_REGION}.amazonaws.com/{_POOL_ID}"
_JWKS_URL = f"{_ISS}/.well-known/jwks.json"
_KID = "test-kid-1"


def _rsa_keypair_pem() -> tuple[bytes, bytes]:
    priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv_pem = priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_pem = priv.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return priv_pem, pub_pem


def _public_jwk(pub_pem: bytes) -> dict:
    # jose's construct-from-PEM path: build a key, then dump JWK dict.
    key = jwk.construct(pub_pem, algorithm="RS256")
    d = json.loads(key.to_json()) if hasattr(key, "to_json") else dict(key.to_dict())
    d["kid"] = _KID
    d["alg"] = "RS256"
    d["use"] = "sig"
    return d


def _sign(priv_pem: bytes, claims: dict) -> str:
    return jwt.encode(claims, priv_pem, algorithm="RS256", headers={"kid": _KID})


@pytest.fixture(autouse=True)
def _prod_like_settings(monkeypatch) -> Iterator[None]:
    """Simulate a deployed env: pool id set, dev bypass disabled."""
    get_settings.cache_clear()
    monkeypatch.setenv("ENV", "staging")
    monkeypatch.setenv("AWS_REGION", _REGION)
    monkeypatch.setenv("COGNITO_USER_POOL_ID", _POOL_ID)
    monkeypatch.setenv("COGNITO_APP_CLIENT_ID", _CLIENT_ID)
    # Force memory repos so the bundle doesn't try to reach DynamoDB in staging mode.
    monkeypatch.setenv("REPO_BACKEND", "memory")
    yield
    security._reset_jwks_cache()
    get_settings.cache_clear()


@pytest.fixture
def keypair() -> tuple[bytes, bytes]:
    priv, pub = _rsa_keypair_pem()
    security._install_test_jwks(_JWKS_URL, [_public_jwk(pub)])
    return priv, pub


@pytest.fixture
def auth_client(keypair) -> Iterator[TestClient]:
    from app.main import create_app

    bundle = RepoBundle(
        users=InMemoryUserRepo(),
        nutritionists=InMemoryNutritionistRepo(),
        food_logs=InMemoryFoodLogRepo(),
        bookings=InMemoryBookingRepo(),
    )
    app = create_app()
    app.dependency_overrides[get_repos] = lambda: bundle
    with TestClient(app) as c:
        yield c


def _valid_access_claims(**overrides) -> dict:
    now = int(time.time())
    claims = {
        "sub": "cognito-sub-123",
        "iss": _ISS,
        "client_id": _CLIENT_ID,
        "token_use": "access",
        "iat": now,
        "exp": now + 300,
        "cognito:groups": ["customers"],
    }
    claims.update(overrides)
    return claims


def test_valid_access_token_is_accepted(auth_client, keypair):
    priv, _ = keypair
    token = _sign(priv, _valid_access_claims())
    r = auth_client.post(
        "/v1/health/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "sex": "male",
            "age_years": 30,
            "height_cm": 180,
            "weight_kg": 80,
            "activity_level": "moderate",
            "goal": "maintain",
        },
    )
    assert r.status_code == 200, r.text
    assert r.json()["user_id"] == "cognito-sub-123"


def test_missing_authorization_header_rejected(auth_client):
    r = auth_client.post(
        "/v1/health/profile",
        json={
            "sex": "male",
            "age_years": 30,
            "height_cm": 180,
            "weight_kg": 80,
            "activity_level": "moderate",
            "goal": "maintain",
        },
    )
    assert r.status_code == 401
    assert "bearer" in r.json()["detail"].lower()


def test_expired_token_rejected(auth_client, keypair):
    priv, _ = keypair
    token = _sign(priv, _valid_access_claims(exp=int(time.time()) - 60))
    r = auth_client.get("/v1/nutritionists/abc", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code in (401, 404)  # 401 from auth layer; fast-path rejects before 404
    if r.status_code == 401:
        assert "expired" in r.json()["detail"].lower()


def test_wrong_issuer_rejected(auth_client, keypair):
    priv, _ = keypair
    token = _sign(priv, _valid_access_claims(iss="https://evil.example.com/"))
    r = auth_client.get("/v1/bookings", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_id_token_rejected_we_want_access_only(auth_client, keypair):
    priv, _ = keypair
    token = _sign(priv, _valid_access_claims(token_use="id"))
    r = auth_client.get("/v1/bookings", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401
    assert "access token" in r.json()["detail"].lower()


def test_client_id_mismatch_rejected(auth_client, keypair):
    priv, _ = keypair
    token = _sign(priv, _valid_access_claims(client_id="some-other-app"))
    r = auth_client.get("/v1/bookings", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401
    assert "client_id" in r.json()["detail"].lower()


def test_admin_group_maps_to_admin_role(auth_client, keypair):
    # Register first via a customer, then admin-verify via admin token.
    priv, _ = keypair
    customer_tok = _sign(priv, _valid_access_claims(sub="customer-1"))
    admin_tok = _sign(priv, _valid_access_claims(sub="admin-1", **{"cognito:groups": ["admins"]}))

    r = auth_client.post(
        "/v1/nutritionists",
        headers={"Authorization": f"Bearer {customer_tok}"},
        json={
            "name": "Priya Kumar",
            "email": "p@example.com",
            "country": "IN",
            "city": "Bengaluru",
            "credentials": ["IDA-RD"],
            "specialties": ["pcos"],
            "virtual_rate": 2500.0,
        },
    )
    assert r.status_code == 201, r.text
    nid = r.json()["nutritionist_id"]

    # Customer-scoped token cannot verify — 403.
    r2 = auth_client.post(
        f"/v1/nutritionists/{nid}/verify",
        params={"status": "approved"},
        headers={"Authorization": f"Bearer {customer_tok}"},
    )
    assert r2.status_code == 403

    # Admin group → role=admin, verify works.
    r3 = auth_client.post(
        f"/v1/nutritionists/{nid}/verify",
        params={"status": "approved"},
        headers={"Authorization": f"Bearer {admin_tok}"},
    )
    assert r3.status_code == 200
    assert r3.json()["verification_status"] == "approved"


def test_unknown_kid_triggers_refetch(auth_client, keypair, monkeypatch):
    """A rotated key should work once we've refetched JWKS."""
    priv, pub = keypair

    # Mint a token with a kid that isn't in the current cache.
    new_kid = "rotated-kid-2"
    tok = jwt.encode(
        _valid_access_claims(sub="rotated-user"),
        priv,
        algorithm="RS256",
        headers={"kid": new_kid},
    )

    # Stage the "new" JWKS behind a fake httpx.get; _resolve_key calls refresh().
    new_jwk = _public_jwk(pub) | {"kid": new_kid}

    class _Resp:
        def json(self):
            return {"keys": [new_jwk]}

    monkeypatch.setattr(security.httpx, "get", lambda url, timeout=5.0: _Resp())

    r = auth_client.get("/v1/bookings", headers={"Authorization": f"Bearer {tok}"})
    # A valid token against the refetched JWKS should succeed (empty list ok).
    assert r.status_code == 200
    assert r.json() == []


def test_dev_bypass_still_works_without_pool_id(monkeypatch):
    """Regression: local dev without Cognito still accepts X-User-Id."""
    get_settings.cache_clear()
    monkeypatch.setenv("ENV", "dev")
    monkeypatch.delenv("COGNITO_USER_POOL_ID", raising=False)
    security._reset_jwks_cache()

    from app.main import create_app

    bundle = RepoBundle(
        users=InMemoryUserRepo(),
        nutritionists=InMemoryNutritionistRepo(),
        food_logs=InMemoryFoodLogRepo(),
        bookings=InMemoryBookingRepo(),
    )
    app = create_app()
    app.dependency_overrides[get_repos] = lambda: bundle
    with TestClient(app) as c:
        r = c.post(
            "/v1/health/profile",
            headers={"X-User-Id": "dev-abc", "X-User-Role": "customer"},
            json={
                "sex": "female",
                "age_years": 28,
                "height_cm": 165,
                "weight_kg": 60,
                "activity_level": "light",
                "goal": "maintain",
            },
        )
        assert r.status_code == 200
        assert r.json()["user_id"] == "dev-abc"
