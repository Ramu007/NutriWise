"""Moto-backed integration tests — exercises the real DynamoDB code path.

Unit tests run against in-memory repos for speed. These tests spin up fake
DynamoDB tables via `moto` with the same schema the CDK stack provisions, so
we catch Decimal/float round-trips, GSI projections, TTL attribute handling,
and query-condition mistakes that the memory backend can't reveal.
"""
from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import boto3
import pytest
from fastapi.testclient import TestClient
from moto import mock_aws

from app.deps import get_repos
from app.repositories.base import RepoBundle
from app.repositories.dynamo import (
    DynamoBookingRepo,
    DynamoFoodLogRepo,
    DynamoNutritionistRepo,
    DynamoUserRepo,
)

_REGION = "us-east-1"
_USERS_TABLE = "nutriwise-users-test"
_NUTS_TABLE = "nutriwise-nutritionists-test"
_FOOD_LOGS_TABLE = "nutriwise-food-logs-test"
_BOOKINGS_TABLE = "nutriwise-bookings-test"


def _create_tables(client) -> None:
    """Mirror the CDK schema — keep in sync with infra/nutriwise_cdk/data_stack.py."""
    client.create_table(
        TableName=_USERS_TABLE,
        AttributeDefinitions=[{"AttributeName": "user_id", "AttributeType": "S"}],
        KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
        BillingMode="PAY_PER_REQUEST",
    )
    client.create_table(
        TableName=_NUTS_TABLE,
        AttributeDefinitions=[
            {"AttributeName": "nutritionist_id", "AttributeType": "S"},
            {"AttributeName": "country", "AttributeType": "S"},
            {"AttributeName": "city", "AttributeType": "S"},
        ],
        KeySchema=[{"AttributeName": "nutritionist_id", "KeyType": "HASH"}],
        BillingMode="PAY_PER_REQUEST",
        GlobalSecondaryIndexes=[
            {
                "IndexName": "by_country_city",
                "KeySchema": [
                    {"AttributeName": "country", "KeyType": "HASH"},
                    {"AttributeName": "city", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "KEYS_ONLY"},
            }
        ],
    )
    client.create_table(
        TableName=_FOOD_LOGS_TABLE,
        AttributeDefinitions=[
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "logged_at", "AttributeType": "S"},
        ],
        KeySchema=[
            {"AttributeName": "user_id", "KeyType": "HASH"},
            {"AttributeName": "logged_at", "KeyType": "RANGE"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    client.create_table(
        TableName=_BOOKINGS_TABLE,
        AttributeDefinitions=[
            {"AttributeName": "booking_id", "AttributeType": "S"},
            {"AttributeName": "nutritionist_id", "AttributeType": "S"},
            {"AttributeName": "starts_at", "AttributeType": "S"},
            {"AttributeName": "user_id", "AttributeType": "S"},
        ],
        KeySchema=[{"AttributeName": "booking_id", "KeyType": "HASH"}],
        BillingMode="PAY_PER_REQUEST",
        GlobalSecondaryIndexes=[
            {
                "IndexName": "by_nutritionist_start",
                "KeySchema": [
                    {"AttributeName": "nutritionist_id", "KeyType": "HASH"},
                    {"AttributeName": "starts_at", "KeyType": "RANGE"},
                ],
                "Projection": {
                    "ProjectionType": "INCLUDE",
                    "NonKeyAttributes": ["duration_minutes", "status"],
                },
            },
            {
                "IndexName": "by_user_start",
                "KeySchema": [
                    {"AttributeName": "user_id", "KeyType": "HASH"},
                    {"AttributeName": "starts_at", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "KEYS_ONLY"},
            },
        ],
    )


@pytest.fixture
def dynamo_client() -> Iterator[TestClient]:
    """TestClient wired to DynamoRepo bundle backed by a moto DynamoDB."""
    # moto reads AWS creds from env; stub them so boto3 doesn't try the metadata service.
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = _REGION
    os.environ.setdefault("ENV", "dev")
    os.environ.pop("COGNITO_USER_POOL_ID", None)

    with mock_aws():
        ddb = boto3.client("dynamodb", region_name=_REGION)
        _create_tables(ddb)

        from app.main import create_app  # import inside so env is set first

        bundle = RepoBundle(
            users=DynamoUserRepo(_USERS_TABLE, _REGION),
            nutritionists=DynamoNutritionistRepo(_NUTS_TABLE, _REGION),
            food_logs=DynamoFoodLogRepo(_FOOD_LOGS_TABLE, _REGION),
            bookings=DynamoBookingRepo(_BOOKINGS_TABLE, _REGION),
        )
        app = create_app()
        app.dependency_overrides[get_repos] = lambda: bundle
        with TestClient(app) as c:
            yield c


@pytest.fixture
def customer_headers() -> dict[str, str]:
    return {"X-User-Id": "user-dyn", "X-User-Role": "customer"}


@pytest.fixture
def admin_headers() -> dict[str, str]:
    return {"X-User-Id": "admin-dyn", "X-User-Role": "admin"}


def _nut_payload(**overrides) -> dict:
    body = {
        "name": "Priya Kumar",
        "email": "priya@example.com",
        "country": "IN",
        "city": "Bengaluru",
        "credentials": ["IDA-RD"],
        "credential_doc_urls": ["https://example.com/doc.pdf"],
        "specialties": ["pcos"],
        "languages": ["en", "hi"],
        "bio": "10+ years in clinical nutrition.",
        "virtual_rate": 2500.0,
        "in_home_rate": 4500.0,
        "kitchen_audit_rate": 6000.0,
    }
    body.update(overrides)
    return body


def test_nutritionist_register_fetch_roundtrips_floats(dynamo_client, customer_headers):
    """Rates are floats — regression guard for the Decimal↔float conversion."""
    r = dynamo_client.post("/v1/nutritionists", json=_nut_payload(), headers=customer_headers)
    assert r.status_code == 201, r.text
    nid = r.json()["nutritionist_id"]

    r2 = dynamo_client.get(f"/v1/nutritionists/{nid}")
    assert r2.status_code == 200
    body = r2.json()
    assert body["virtual_rate"] == 2500.0
    assert body["in_home_rate"] == 4500.0
    assert body["kitchen_audit_rate"] == 6000.0


def test_search_uses_scan_and_respects_filters(
    dynamo_client, customer_headers, admin_headers
):
    # Approved one in IN/Bengaluru.
    r1 = dynamo_client.post("/v1/nutritionists", json=_nut_payload(), headers=customer_headers)
    nid = r1.json()["nutritionist_id"]
    dynamo_client.post(
        f"/v1/nutritionists/{nid}/verify",
        params={"status": "approved"},
        headers=admin_headers,
    )
    # Pending one in US/Boston shouldn't appear in the default (only_approved=True) search.
    dynamo_client.post(
        "/v1/nutritionists",
        json=_nut_payload(name="Sarah", email="s@example.com", country="US", city="Boston"),
        headers=customer_headers,
    )
    r = dynamo_client.get("/v1/nutritionists", params={"country": "IN"})
    assert r.status_code == 200
    results = r.json()
    assert len(results) == 1
    assert results[0]["nutritionist_id"] == nid


def test_booking_flow_queries_gsi(dynamo_client, customer_headers, admin_headers):
    r = dynamo_client.post(
        "/v1/nutritionists",
        json=_nut_payload(country="US", city="Boston", virtual_rate=80.0),
        headers=customer_headers,
    )
    nid = r.json()["nutritionist_id"]
    dynamo_client.post(
        f"/v1/nutritionists/{nid}/verify",
        params={"status": "approved"},
        headers=admin_headers,
    )

    base = datetime.now(UTC) + timedelta(days=2)
    r2 = dynamo_client.post(
        "/v1/bookings",
        json={
            "nutritionist_id": nid,
            "type": "virtual",
            "starts_at": base.isoformat(),
            "duration_minutes": 60,
        },
        headers=customer_headers,
    )
    assert r2.status_code == 201, r2.text

    # Overlap check goes through the by_nutritionist_start GSI.
    r3 = dynamo_client.post(
        "/v1/bookings",
        json={
            "nutritionist_id": nid,
            "type": "virtual",
            "starts_at": (base + timedelta(minutes=30)).isoformat(),
            "duration_minutes": 45,
        },
        headers=customer_headers,
    )
    assert r3.status_code == 409

    # list_mine goes through by_user_start GSI.
    r4 = dynamo_client.get("/v1/bookings", headers=customer_headers)
    assert r4.status_code == 200
    assert len(r4.json()) == 1


def test_food_log_sets_ttl_and_queries_by_day(dynamo_client, customer_headers):
    now = datetime.now(UTC)
    r = dynamo_client.post(
        "/v1/food/logs",
        json={
            "entry_id": "",  # router stamps a uuid when falsy
            "user_id": "ignored",  # overwritten by principal
            "logged_at": now.isoformat(),
            "meal": "breakfast",
            "items": [
                {
                    "name": "oats",
                    "serving": "80g",
                    "kcal": 310.0,
                    "protein_g": 11.0,
                    "carbs_g": 54.0,
                    "fat_g": 5.0,
                }
            ],
            "source": "manual",
        },
        headers=customer_headers,
    )
    assert r.status_code == 201, r.text

    # Raw table read to confirm the TTL attribute was populated.
    ddb = boto3.resource("dynamodb", region_name=_REGION)
    items = ddb.Table(_FOOD_LOGS_TABLE).scan()["Items"]
    assert len(items) == 1
    assert "ttl" in items[0]
    # ~2 years out.
    assert int(items[0]["ttl"]) > int((now + timedelta(days=700)).timestamp())

    # Summary now reads the caller's persisted profile — upsert one first.
    dynamo_client.post(
        "/v1/health/profile",
        json={
            "sex": "female",
            "age_years": 30,
            "height_cm": 165,
            "weight_kg": 60,
            "activity_level": "moderate",
            "goal": "maintain",
        },
        headers=customer_headers,
    )
    r2 = dynamo_client.get(
        "/v1/food/summary",
        params={"day": now.date().isoformat()},
        headers=customer_headers,
    )
    assert r2.status_code == 200
    assert r2.json()["total_kcal"] == 310.0
