"""BMI / BMR / TDEE math — the values the product surfaces to users."""
from __future__ import annotations

import pytest

from app.models.health import (
    ActivityLevel,
    HealthProfileIn,
    Sex,
    bmi_category,
    compute_bmi,
    compute_bmr_mifflin,
    compute_tdee,
    daily_target_kcal,
    enrich_profile,
)


def test_bmi_basic():
    # 70kg, 175cm -> 22.9
    assert compute_bmi(70, 175) == 22.9


@pytest.mark.parametrize(
    "bmi,expected",
    [
        (17.0, "underweight"),
        (18.5, "normal"),
        (24.9, "normal"),
        (25.0, "overweight"),
        (29.9, "overweight"),
        (30.0, "obese"),
        (42.0, "obese"),
    ],
)
def test_bmi_category_boundaries(bmi: float, expected: str):
    assert bmi_category(bmi) == expected


def test_bmr_mifflin_male():
    # Classic fixture: 30-yr-old, 80kg, 180cm male -> 1780.0
    assert compute_bmr_mifflin(Sex.male, 80, 180, 30) == 1780.0


def test_bmr_mifflin_female_lower_than_male():
    # Same size/age but female should be 166 kcal lower (5 vs -161).
    male = compute_bmr_mifflin(Sex.male, 70, 170, 35)
    female = compute_bmr_mifflin(Sex.female, 70, 170, 35)
    assert male - female == pytest.approx(166.0, rel=1e-3)


def test_tdee_activity_scales_correctly():
    bmr = 1500.0
    assert compute_tdee(bmr, ActivityLevel.sedentary) == pytest.approx(1800.0)
    assert compute_tdee(bmr, ActivityLevel.very_active) == pytest.approx(2850.0)


@pytest.mark.parametrize(
    "goal,expected_delta",
    [("lose", -500), ("maintain", 0), ("gain", 300)],
)
def test_daily_target_matches_goal(goal: str, expected_delta: int):
    assert daily_target_kcal(2000, goal) - 2000 == expected_delta


def test_enrich_profile_populates_all_derived_fields():
    p = HealthProfileIn(
        sex=Sex.male,
        age_years=30,
        height_cm=180,
        weight_kg=80,
        activity_level=ActivityLevel.moderate,
        goal="lose",
    )
    out = enrich_profile("u-1", p)
    assert out.user_id == "u-1"
    assert out.bmi == pytest.approx(24.7, abs=0.1)
    assert out.bmi_category == "normal"
    assert out.bmr_kcal == 1780.0
    assert out.tdee_kcal == pytest.approx(1780.0 * 1.55, rel=1e-3)
    assert out.daily_target_kcal == pytest.approx(out.tdee_kcal - 500, rel=1e-3)


def test_profile_sanitizes_allergies_and_conditions():
    p = HealthProfileIn(
        sex=Sex.female,
        age_years=28,
        height_cm=165,
        weight_kg=60,
        allergies=["  Peanuts ", "peanuts", "Shellfish", ""],
        health_conditions=["PCOS", "pcos "],
    )
    # Dedup + lowercase + strip + sorted.
    assert p.allergies == ["peanuts", "shellfish"]
    assert p.health_conditions == ["pcos"]


@pytest.mark.parametrize("bad_age", [12, 111, 0, -1])
def test_age_range_validation(bad_age: int):
    with pytest.raises(ValueError):
        HealthProfileIn(
            sex=Sex.male, age_years=bad_age, height_cm=170, weight_kg=65
        )


@pytest.mark.parametrize("bad_height", [49, 260, 0])
def test_height_range_validation(bad_height: float):
    with pytest.raises(ValueError):
        HealthProfileIn(
            sex=Sex.male, age_years=30, height_cm=bad_height, weight_kg=65
        )
