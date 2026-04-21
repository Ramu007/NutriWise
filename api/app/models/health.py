"""Health profile models — BMI, BMR, TDEE calculations."""
from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class Sex(StrEnum):
    male = "male"
    female = "female"


class ActivityLevel(StrEnum):
    sedentary = "sedentary"
    light = "light"
    moderate = "moderate"
    active = "active"
    very_active = "very_active"


# Multiplier for Mifflin-St Jeor TDEE. Standard published values.
ACTIVITY_MULTIPLIER: dict[ActivityLevel, float] = {
    ActivityLevel.sedentary: 1.2,
    ActivityLevel.light: 1.375,
    ActivityLevel.moderate: 1.55,
    ActivityLevel.active: 1.725,
    ActivityLevel.very_active: 1.9,
}


class DietaryPref(StrEnum):
    omnivore = "omnivore"
    vegetarian = "vegetarian"
    vegan = "vegan"
    jain = "jain"  # India-specific: no root vegetables, no onion/garlic
    eggetarian = "eggetarian"  # India-specific: vegetarian + eggs
    pescatarian = "pescatarian"
    keto = "keto"
    halal = "halal"
    kosher = "kosher"


class HealthProfileIn(BaseModel):
    sex: Sex
    age_years: int = Field(ge=13, le=110)
    height_cm: float = Field(gt=50, lt=260)
    weight_kg: float = Field(gt=20, lt=400)
    activity_level: ActivityLevel = ActivityLevel.moderate
    goal: Literal["lose", "maintain", "gain"] = "maintain"

    dietary_preferences: list[DietaryPref] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    health_conditions: list[str] = Field(default_factory=list)

    country: Literal["US", "IN"] = "US"

    @model_validator(mode="after")
    def _sanitize(self) -> HealthProfileIn:
        self.allergies = sorted({a.strip().lower() for a in self.allergies if a.strip()})
        self.health_conditions = sorted(
            {c.strip().lower() for c in self.health_conditions if c.strip()}
        )
        return self


class HealthProfileOut(HealthProfileIn):
    user_id: str
    bmi: float
    bmi_category: str
    bmr_kcal: float
    tdee_kcal: float
    daily_target_kcal: float


def compute_bmi(weight_kg: float, height_cm: float) -> float:
    h_m = height_cm / 100.0
    return round(weight_kg / (h_m * h_m), 1)


def bmi_category(bmi: float) -> str:
    # WHO adult thresholds. Noting they differ slightly in India (APAC cutoffs) —
    # we show the WHO baseline and let the nutritionist contextualize.
    if bmi < 18.5:
        return "underweight"
    if bmi < 25:
        return "normal"
    if bmi < 30:
        return "overweight"
    return "obese"


def compute_bmr_mifflin(sex: Sex, weight_kg: float, height_cm: float, age_years: int) -> float:
    # Mifflin-St Jeor (1990): more accurate than Harris-Benedict for modern populations.
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age_years
    return round(base + (5 if sex == Sex.male else -161), 1)


def compute_tdee(bmr: float, activity: ActivityLevel) -> float:
    return round(bmr * ACTIVITY_MULTIPLIER[activity], 1)


def daily_target_kcal(tdee: float, goal: str) -> float:
    if goal == "lose":
        return round(tdee - 500, 1)  # ~0.5 kg/week deficit
    if goal == "gain":
        return round(tdee + 300, 1)
    return tdee


def enrich_profile(user_id: str, p: HealthProfileIn) -> HealthProfileOut:
    bmi = compute_bmi(p.weight_kg, p.height_cm)
    bmr = compute_bmr_mifflin(p.sex, p.weight_kg, p.height_cm, p.age_years)
    tdee = compute_tdee(bmr, p.activity_level)
    target = daily_target_kcal(tdee, p.goal)
    return HealthProfileOut(
        **p.model_dump(),
        user_id=user_id,
        bmi=bmi,
        bmi_category=bmi_category(bmi),
        bmr_kcal=bmr,
        tdee_kcal=tdee,
        daily_target_kcal=target,
    )
