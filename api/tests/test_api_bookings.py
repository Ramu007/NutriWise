"""End-to-end: /v1/bookings."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta


def _register_approved(client, customer_headers, admin_headers, **nut_overrides) -> str:
    body = {
        "name": "Sarah",
        "email": "sarah@example.com",
        "country": "US",
        "city": "Boston",
        "credentials": ["RDN"],
        "credential_doc_urls": ["https://example.com/doc.pdf"],
        "specialties": ["sports"],
        "languages": ["en"],
        "virtual_rate": 80,
        "in_home_rate": 180,
    }
    body.update(nut_overrides)
    r = client.post("/v1/nutritionists", json=body, headers=customer_headers)
    nid = r.json()["nutritionist_id"]
    client.post(
        f"/v1/nutritionists/{nid}/verify",
        params={"status": "approved"},
        headers=admin_headers,
    )
    return nid


def test_create_booking_happy_path(client, customer_headers, admin_headers):
    nid = _register_approved(client, customer_headers, admin_headers)
    start = (datetime.now(UTC) + timedelta(days=2)).isoformat()
    r = client.post(
        "/v1/bookings",
        json={
            "nutritionist_id": nid,
            "type": "virtual",
            "starts_at": start,
            "duration_minutes": 45,
            "notes": "First consult",
        },
        headers=customer_headers,
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["price"] == 80.0
    assert body["currency"] == "USD"
    assert body["status"] == "pending"


def test_booking_conflict_rejected(client, customer_headers, admin_headers):
    nid = _register_approved(client, customer_headers, admin_headers)
    base = datetime.now(UTC) + timedelta(days=3)

    r = client.post(
        "/v1/bookings",
        json={
            "nutritionist_id": nid,
            "type": "virtual",
            "starts_at": base.isoformat(),
            "duration_minutes": 60,
        },
        headers=customer_headers,
    )
    assert r.status_code == 201

    r2 = client.post(
        "/v1/bookings",
        json={
            "nutritionist_id": nid,
            "type": "virtual",
            "starts_at": (base + timedelta(minutes=30)).isoformat(),
            "duration_minutes": 45,
        },
        headers=customer_headers,
    )
    assert r2.status_code == 409


def test_cannot_book_unapproved(client, customer_headers):
    # Register without approving.
    body = {
        "name": "Pending",
        "email": "p@example.com",
        "country": "US",
        "city": "NYC",
        "credentials": ["RDN"],
        "virtual_rate": 60,
    }
    r = client.post("/v1/nutritionists", json=body, headers=customer_headers)
    nid = r.json()["nutritionist_id"]
    start = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    r2 = client.post(
        "/v1/bookings",
        json={"nutritionist_id": nid, "type": "virtual", "starts_at": start, "duration_minutes": 45},
        headers=customer_headers,
    )
    assert r2.status_code == 409


def test_cancel_flow(client, customer_headers, admin_headers):
    nid = _register_approved(client, customer_headers, admin_headers)
    start = (datetime.now(UTC) + timedelta(days=2)).isoformat()
    r = client.post(
        "/v1/bookings",
        json={"nutritionist_id": nid, "type": "virtual", "starts_at": start, "duration_minutes": 45},
        headers=customer_headers,
    )
    bid = r.json()["booking_id"]
    r2 = client.post(f"/v1/bookings/{bid}/cancel", headers=customer_headers)
    assert r2.status_code == 200
    assert r2.json()["status"] == "cancelled"

    # Double cancel -> 409.
    r3 = client.post(f"/v1/bookings/{bid}/cancel", headers=customer_headers)
    assert r3.status_code == 409


def test_commission_preview(client, customer_headers, admin_headers):
    nid = _register_approved(client, customer_headers, admin_headers)
    start = (datetime.now(UTC) + timedelta(days=5)).isoformat()
    r = client.post(
        "/v1/bookings",
        json={"nutritionist_id": nid, "type": "virtual", "starts_at": start, "duration_minutes": 45},
        headers=customer_headers,
    )
    bid = r.json()["booking_id"]
    r2 = client.get(f"/v1/bookings/{bid}/commission", headers=customer_headers)
    assert r2.status_code == 200
    body = r2.json()
    assert body["gross"] == 80.0
    assert body["platform_commission"] == 12.0
    assert body["nutritionist_payout"] == 68.0
