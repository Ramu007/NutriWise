"""End-to-end: /v1/nutritionists."""
from __future__ import annotations


def _valid_nutritionist_payload(**overrides) -> dict:
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
        "virtual_rate": 2500,
        "in_home_rate": 4500,
        "kitchen_audit_rate": 6000,
    }
    body.update(overrides)
    return body


def test_register_and_fetch(client, customer_headers):
    r = client.post("/v1/nutritionists", json=_valid_nutritionist_payload(), headers=customer_headers)
    assert r.status_code == 201, r.text
    nid = r.json()["nutritionist_id"]
    assert r.json()["verification_status"] == "pending"

    r2 = client.get(f"/v1/nutritionists/{nid}")
    assert r2.status_code == 200
    assert r2.json()["nutritionist_id"] == nid


def test_search_hides_pending_by_default(client, customer_headers):
    r = client.post("/v1/nutritionists", json=_valid_nutritionist_payload(), headers=customer_headers)
    assert r.status_code == 201
    # Default search excludes non-approved.
    r2 = client.get("/v1/nutritionists")
    assert r2.status_code == 200
    assert r2.json() == []


def test_admin_can_verify_then_searchable(client, customer_headers, admin_headers):
    r = client.post("/v1/nutritionists", json=_valid_nutritionist_payload(), headers=customer_headers)
    nid = r.json()["nutritionist_id"]
    r2 = client.post(
        f"/v1/nutritionists/{nid}/verify",
        params={"status": "approved"},
        headers=admin_headers,
    )
    assert r2.status_code == 200
    assert r2.json()["verification_status"] == "approved"

    r3 = client.get("/v1/nutritionists", params={"country": "IN"})
    assert r3.status_code == 200
    assert len(r3.json()) == 1


def test_non_admin_cannot_verify(client, customer_headers):
    r = client.post("/v1/nutritionists", json=_valid_nutritionist_payload(), headers=customer_headers)
    nid = r.json()["nutritionist_id"]
    r2 = client.post(
        f"/v1/nutritionists/{nid}/verify",
        params={"status": "approved"},
        headers=customer_headers,
    )
    assert r2.status_code == 403


def test_register_rejects_empty_credentials(client, customer_headers):
    r = client.post(
        "/v1/nutritionists",
        json=_valid_nutritionist_payload(credentials=[]),
        headers=customer_headers,
    )
    assert r.status_code == 422
