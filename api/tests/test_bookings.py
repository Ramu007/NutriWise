"""Booking conflict detection + pricing."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.models.booking import BookingOut, BookingStatus, BookingType
from app.models.nutritionist import (
    Credential,
    NutritionistOut,
    VerificationStatus,
)
from app.services.bookings import conflicts_with_existing
from app.services.pricing import commission, currency_for, rate_for


def _bk(start: datetime, duration: int = 45, nid: str = "n-1", status: BookingStatus = BookingStatus.confirmed) -> BookingOut:
    return BookingOut(
        booking_id=f"b-{start.isoformat()}",
        user_id="u-1",
        nutritionist_id=nid,
        type=BookingType.virtual,
        starts_at=start,
        duration_minutes=duration,
        status=status,
        price=50.0,
        currency="USD",
        created_at=datetime.now(UTC),
        notes="",
    )


def test_no_conflict_when_back_to_back():
    base = datetime(2026, 5, 1, 10, 0, tzinfo=UTC)
    existing = [_bk(base, duration=45)]
    # Next slot starts exactly when prior ends.
    assert not conflicts_with_existing("n-1", base + timedelta(minutes=45), 45, existing)


def test_conflict_on_overlap():
    base = datetime(2026, 5, 1, 10, 0, tzinfo=UTC)
    existing = [_bk(base, duration=60)]
    assert conflicts_with_existing("n-1", base + timedelta(minutes=30), 30, existing)


def test_conflict_ignores_other_nutritionists():
    base = datetime(2026, 5, 1, 10, 0, tzinfo=UTC)
    existing = [_bk(base, duration=60, nid="n-other")]
    assert not conflicts_with_existing("n-1", base, 45, existing)


def test_cancelled_booking_does_not_conflict():
    base = datetime(2026, 5, 1, 10, 0, tzinfo=UTC)
    existing = [_bk(base, duration=60, status=BookingStatus.cancelled)]
    assert not conflicts_with_existing("n-1", base, 45, existing)


def _n(**kwargs) -> NutritionistOut:
    base = dict(
        nutritionist_id="n-1", name="Alex", email="a@b.com", country="US", city="NYC",
        credentials=[Credential.rdn], credential_doc_urls=[], specialties=[],
        languages=["en"], bio="",
        virtual_rate=80.0, in_home_rate=180.0, kitchen_audit_rate=None,
        verification_status=VerificationStatus.approved,
        rating_avg=0, rating_count=0,
        created_at=datetime.now(UTC),
    )
    base.update(kwargs)
    return NutritionistOut(**base)


def test_rate_for_picks_correct_field():
    n = _n()
    assert rate_for(n, BookingType.virtual) == 80.0
    assert rate_for(n, BookingType.in_home) == 180.0


def test_rate_for_raises_when_service_not_offered():
    n = _n(kitchen_audit_rate=None)
    with pytest.raises(ValueError):
        rate_for(n, BookingType.kitchen_audit)


@pytest.mark.parametrize("country,expected", [("US", "USD"), ("IN", "INR")])
def test_currency_for_country(country: str, expected: str):
    assert currency_for(country) == expected


def test_commission_is_15_percent():
    assert commission(100.0) == 15.0
    assert commission(85.0) == 12.75
