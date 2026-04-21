"""End-to-end: /v1/health/profile."""
from __future__ import annotations


def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "version" in body


def test_upsert_profile_returns_derived_fields(client, customer_headers):
    payload = {
        "sex": "male",
        "age_years": 30,
        "height_cm": 180,
        "weight_kg": 80,
        "activity_level": "moderate",
        "goal": "lose",
        "country": "US",
    }
    r = client.post("/v1/health/profile", json=payload, headers=customer_headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["user_id"] == "user-abc"
    assert body["bmr_kcal"] == 1780.0
    assert body["bmi_category"] == "normal"
    assert body["daily_target_kcal"] < body["tdee_kcal"]  # "lose" subtracts 500


def test_profile_rejects_invalid_payload(client, customer_headers):
    r = client.post(
        "/v1/health/profile",
        json={"sex": "male", "age_years": 5, "height_cm": 170, "weight_kg": 60},
        headers=customer_headers,
    )
    assert r.status_code == 422
