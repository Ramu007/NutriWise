"""Session pricing rules — kept in one place so ops can tune without chasing routers."""
from __future__ import annotations

from app.models.booking import BookingType
from app.models.nutritionist import NutritionistOut

# Platform commission taken from the nutritionist's rate on each booking.
PLATFORM_COMMISSION_PCT = 0.15


def rate_for(nutritionist: NutritionistOut, booking_type: BookingType) -> float:
    if booking_type == BookingType.virtual:
        return nutritionist.virtual_rate
    if booking_type == BookingType.in_home:
        if nutritionist.in_home_rate is None:
            raise ValueError("nutritionist does not offer in-home sessions")
        return nutritionist.in_home_rate
    if booking_type == BookingType.kitchen_audit:
        if nutritionist.kitchen_audit_rate is None:
            raise ValueError("nutritionist does not offer kitchen audits")
        return nutritionist.kitchen_audit_rate
    raise ValueError(f"unknown booking type: {booking_type}")


def currency_for(country: str) -> str:
    return "INR" if country == "IN" else "USD"


def commission(amount: float) -> float:
    return round(amount * PLATFORM_COMMISSION_PCT, 2)
