"""S3 presigned uploads + analyze-by-key — moto-backed, no real AWS calls.

`/analyze-key` hits Bedrock under the hood; we monkeypatch the vision call
at the router's import site so the test only exercises our S3 plumbing.
"""
from __future__ import annotations

from collections.abc import Iterator

import boto3
import pytest
from fastapi.testclient import TestClient
from moto import mock_aws

from app.deps import get_repos
from app.models.food import FoodPhotoAnalysis
from app.repositories.base import RepoBundle
from app.repositories.memory import (
    InMemoryBookingRepo,
    InMemoryFoodLogRepo,
    InMemoryNutritionistRepo,
    InMemoryUserRepo,
)

_REGION = "us-east-1"
_BUCKET = "nutriwise-food-photos-test"


@pytest.fixture
def s3_client(monkeypatch) -> Iterator[TestClient]:
    # Stub creds so boto3 inside the app doesn't try the metadata service.
    # Override any shell AWS creds/region so boto3 + moto agree.
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", _REGION)
    monkeypatch.setenv("AWS_REGION", _REGION)
    monkeypatch.delenv("AWS_PROFILE", raising=False)
    monkeypatch.setenv("ENV", "dev")
    monkeypatch.delenv("COGNITO_USER_POOL_ID", raising=False)
    monkeypatch.setenv("FOOD_PHOTOS_BUCKET", _BUCKET)

    # Settings is lru_cached; clear so the new bucket name is picked up.
    from app.core.config import get_settings

    get_settings.cache_clear()

    with mock_aws():
        boto3.client("s3", region_name=_REGION).create_bucket(Bucket=_BUCKET)

        from app.main import create_app
        from app.routers import food as food_router

        # Stub the vision call — we don't hit Bedrock in tests.
        def _fake_analyze(data, media_type, user_hint=None, settings=None):
            return FoodPhotoAnalysis(
                items=[],
                total_kcal=0.0,
                total_protein_g=0.0,
                total_carbs_g=0.0,
                total_fat_g=0.0,
                notes=f"stub bytes={len(data)} type={media_type} hint={user_hint}",
                model_used="stub",
            )

        monkeypatch.setattr(food_router, "analyze_food_photo", _fake_analyze)

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

    get_settings.cache_clear()


@pytest.fixture
def customer_headers() -> dict[str, str]:
    return {"X-User-Id": "user-up", "X-User-Role": "customer"}


def test_presign_returns_put_url_under_user_prefix(s3_client, customer_headers):
    r = s3_client.post(
        "/v1/food/uploads/presign",
        json={"content_type": "image/jpeg"},
        headers=customer_headers,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["method"] == "PUT"
    assert body["expires_in"] > 0
    assert body["s3_key"].startswith("uploads/user-up/")
    assert body["s3_key"].endswith(".jpg")
    assert body["required_headers"] == {"Content-Type": "image/jpeg"}
    # Presigned URL must be against the configured bucket.
    assert _BUCKET in body["url"]


def test_presign_rejects_unsupported_content_type(s3_client, customer_headers):
    r = s3_client.post(
        "/v1/food/uploads/presign",
        json={"content_type": "application/pdf"},
        headers=customer_headers,
    )
    assert r.status_code == 422


def test_upload_then_analyze_key_roundtrip(s3_client, customer_headers):
    # 1) ask for a presigned URL (shape already asserted in the previous test).
    r = s3_client.post(
        "/v1/food/uploads/presign",
        json={"content_type": "image/png"},
        headers=customer_headers,
    )
    assert r.status_code == 200
    presign = r.json()

    # 2) Put bytes at that key. We use boto3 directly because moto's presigned-
    # URL signer gives back creds that moto's request validator then rejects;
    # the end-to-end HTTP PUT is exercised in live smoke tests, not here.
    fake_png = b"\x89PNG\r\n\x1a\n" + b"x" * 128
    boto3.client("s3", region_name=_REGION).put_object(
        Bucket=_BUCKET,
        Key=presign["s3_key"],
        Body=fake_png,
        ContentType="image/png",
    )

    # 3) analyze by key — the router fetches from S3 and calls our stub analyzer.
    r2 = s3_client.post(
        "/v1/food/analyze-key",
        json={"s3_key": presign["s3_key"], "hint": "breakfast"},
        headers=customer_headers,
    )
    assert r2.status_code == 200, r2.text
    body = r2.json()
    # Our stub echoes the bytes length + hint into `notes`.
    assert str(len(fake_png)) in body["notes"]
    assert "breakfast" in body["notes"]


def test_analyze_key_rejects_cross_user_access(s3_client, customer_headers):
    # Someone else's upload path — 403 even if the object happens to exist.
    r = s3_client.post(
        "/v1/food/analyze-key",
        json={"s3_key": "uploads/another-user/abc.jpg"},
        headers=customer_headers,
    )
    assert r.status_code == 403


def test_analyze_key_missing_object_returns_404(s3_client, customer_headers):
    r = s3_client.post(
        "/v1/food/analyze-key",
        json={"s3_key": "uploads/user-up/nonexistent.jpg"},
        headers=customer_headers,
    )
    assert r.status_code == 404
