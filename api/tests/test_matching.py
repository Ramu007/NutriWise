"""Nutritionist search filters and ranking."""
from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.models.nutritionist import (
    Credential,
    NutritionistOut,
    NutritionistSpecialty,
    VerificationStatus,
)
from app.services.matching import SearchFilters, filter_nutritionists


def _n(**overrides) -> NutritionistOut:
    defaults = dict(
        nutritionist_id="n-1",
        name="Priya Kumar",
        email="priya@example.com",
        country="IN",
        city="Bengaluru",
        credentials=[Credential.ida_rd],
        credential_doc_urls=[],
        specialties=[NutritionistSpecialty.pcos, NutritionistSpecialty.diabetes],
        languages=["en", "hi", "kn"],
        bio="",
        virtual_rate=2500.0,
        in_home_rate=4500.0,
        kitchen_audit_rate=6000.0,
        verification_status=VerificationStatus.approved,
        rating_avg=4.7,
        rating_count=120,
        created_at=datetime.now(UTC),
    )
    defaults.update(overrides)
    return NutritionistOut(**defaults)


@pytest.fixture
def people():
    return [
        _n(nutritionist_id="p1", name="Priya", country="IN", city="Bengaluru", rating_avg=4.9, rating_count=200),
        _n(
            nutritionist_id="p2", name="Maya", country="IN", city="Mumbai",
            rating_avg=4.5, rating_count=50,
            specialties=[NutritionistSpecialty.weight_loss],
            languages=["en", "mr"],
        ),
        _n(
            nutritionist_id="p3", name="Sarah", country="US", city="Boston",
            credentials=[Credential.rdn], rating_avg=4.8, rating_count=300,
            virtual_rate=85.0, in_home_rate=150.0, kitchen_audit_rate=200.0,
            specialties=[NutritionistSpecialty.sports],
            languages=["en"],
        ),
        _n(
            nutritionist_id="p4", name="Pending", country="US", city="NYC",
            verification_status=VerificationStatus.pending,
        ),
    ]


def test_only_approved_filters_pending(people):
    out = filter_nutritionists(people, SearchFilters())
    assert all(n.verification_status == VerificationStatus.approved for n in out)
    assert "p4" not in {n.nutritionist_id for n in out}


def test_country_filter(people):
    out = filter_nutritionists(people, SearchFilters(country="IN"))
    assert {n.nutritionist_id for n in out} == {"p1", "p2"}


def test_specialty_filter(people):
    out = filter_nutritionists(people, SearchFilters(specialty=NutritionistSpecialty.pcos))
    assert [n.nutritionist_id for n in out] == ["p1"]


def test_language_filter(people):
    out = filter_nutritionists(people, SearchFilters(language="mr"))
    assert [n.nutritionist_id for n in out] == ["p2"]


def test_rating_sort_desc(people):
    out = filter_nutritionists(people, SearchFilters(country="IN"))
    assert [n.nutritionist_id for n in out] == ["p1", "p2"]


def test_max_rate_filter(people):
    out = filter_nutritionists(people, SearchFilters(country="US", max_virtual_rate=50.0))
    assert out == []  # Sarah is $85
    out2 = filter_nutritionists(people, SearchFilters(country="US", max_virtual_rate=100.0))
    assert [n.nutritionist_id for n in out2] == ["p3"]


def test_include_pending_when_opt_in(people):
    out = filter_nutritionists(people, SearchFilters(only_approved=False, country="US"))
    assert {n.nutritionist_id for n in out} == {"p3", "p4"}
